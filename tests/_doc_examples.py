"""Helpers for parsing ``CLI Example:`` blocks out of module docstrings.

Used by:
 - ``tests/unit/test_doc_examples.py`` — signature-check pass (no I/O)
 - ``saltext-vmware-integration/test_doc_examples.py`` — live invocation pass

Block shape we recognize::

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_thing.func arg1 key=value
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
import re
import shlex
from collections.abc import Callable

import saltext.vmware.modules as _modules_pkg

_SALT_LINE = re.compile(r"""^\s*salt\s+(?:'[^']*'|"[^"]*"|\S+)\s+(\S+)\s*(.*)$""")
_MODULE_FUNC = re.compile(r"^(?P<mod>[\w]+)\.(?P<func>[\w]+)$")
_KW = re.compile(r"^(?P<k>[A-Za-z_][\w]*)=(?P<v>.+)$")

# Tokens that look like fake managed-object IDs — treat as placeholders even
# without ``<>`` brackets. Matches ``vm-100``, ``cluster-1``, ``domain-c9``,
# ``network-12``, ``host-5``, ``ds-1``, ``rp-1``, ``dvs-1``, etc.
_FAKE_ID = re.compile(r"^[a-z][a-z]*-(?:c?)\d+$")
_LITERAL_CONST = {"true", "false", "null", "True", "False", "None"}


def _looks_like_placeholder_positional(v: str) -> bool:
    """Heuristic: a positional CLI arg is a placeholder unless it's a literal.

    Literals we recognize: number, boolean/null, JSON dict/list, explicit empty.
    """
    if not v:
        return False
    if "<" in v and ">" in v:
        return True
    if v in _LITERAL_CONST:
        return False
    # Numeric literal (int or float, optionally signed).
    try:
        float(v)
        return False
    except ValueError:
        pass
    # JSON dict / list — the user wrote a real shape.
    if v[0] in "{[":
        return False
    # Quoted string the shell would split — treat as literal.
    if v[0] in "'\"" and v[-1] == v[0]:
        return False
    # Everything else (``prod-dvs``, ``MyLib``, ``vm-19``) is a domain object name.
    return True


@dataclasses.dataclass(frozen=True)
class DocExample:
    """One parsed ``salt '*' <mod>.<func> ...`` example line.

    Attributes:
        source_file: path to the .py module the docstring came from.
        virtual_name: the module's ``__virtualname__`` (e.g. ``vmware_nsx_node``).
        func_name: the function name (e.g. ``get``).
        positional: list of positional argument tokens, as written.
        keyword: dict of keyword=value tokens, as written.
        raw: the original ``salt '*' ...`` line for error reporting.
    """

    source_file: str
    virtual_name: str
    func_name: str
    positional: tuple[str, ...]
    keyword: tuple[tuple[str, str], ...]
    raw: str

    @property
    def has_placeholders(self) -> bool:
        """True if any arg is a placeholder (literal ``<x>``, fake ID, or a name).

        For positional args, anything that isn't a clear literal value (number,
        ``true``/``false``/``null``, JSON ``{...}``/``[...]``) is treated as a
        placeholder — in practice positional CLI args almost always name a
        domain object the user must substitute (``prod-dvs``, ``vm-100``,
        ``cluster-1``, ``MyLib``...). For keyword args we're stricter: only
        explicit ``<...>`` or fake-ID shapes count.
        """
        for v in self.positional:
            if _looks_like_placeholder_positional(v):
                return True
        for _, v in self.keyword:
            if "<" in v and ">" in v:
                return True
            if _FAKE_ID.match(v):
                return True
        return False

    @property
    def is_destructive(self) -> bool:
        """Heuristic: function names that mutate state.

        Read-only verbs: ``list``, ``get``, ``info``, ``find``, ``status``, ``current``.
        Anything else (``create_*``, ``delete_*``, ``add_*``, ``set_*``, ``update_*``,
        ``upgrade_*``, ``mount_*``, ``unmount_*``, ``reset``, ``suspend``,
        ``shutdown_*``, ``reboot_*``, ``standby_*``, ``power_*``, ``migrate``,
        ``relocate``, ``apply_*``, ``revert``, ``remove*``, ``deploy_*``, ``expand_*``,
        ``shrink_*``, ``validate``, ``publish_*``, ``sync_*``, ``retry``, ``cancel``,
        ``wait``, ``rename_*``, ``mark_*``, ``join_*``, ``leave_*``,
        ``promote_*``, ``demote_*``, ``register_*``, ``unregister_*``,
        ``enable_*``, ``disable_*``) is destructive.
        """
        f = self.func_name
        read_only_prefixes = ("list", "get", "info", "find", "current")
        read_only_exact = {
            "list_",
            "list",
            "get",
            "info",
            "status",
            "ping",
            "show",
            "system_info",
            "licensing_info",
        }
        if f in read_only_exact:
            return False
        for p in read_only_prefixes:
            if f == p or f.startswith(p + "_"):
                return False
        return True


def _iter_doc_examples_from_module(py_module) -> list[DocExample]:
    """Walk the public callables of *py_module* and yield ``DocExample`` records."""
    out: list[DocExample] = []
    source_file = getattr(py_module, "__file__", "<?>")
    for name, obj in inspect.getmembers(py_module):
        if name.startswith("_"):
            continue
        if not callable(obj):
            continue
        if inspect.getmodule(obj) is not py_module:
            continue
        doc = inspect.getdoc(obj) or ""
        for raw in _parse_salt_lines(doc):
            mf = _MODULE_FUNC.match(raw["target"])
            if not mf:
                continue
            positional, keyword = _split_args(raw["args"])
            out.append(
                DocExample(
                    source_file=source_file,
                    virtual_name=mf.group("mod"),
                    func_name=mf.group("func"),
                    positional=tuple(positional),
                    keyword=tuple(keyword),
                    raw=raw["raw"],
                )
            )
    return out


def _parse_salt_lines(doc: str) -> list[dict]:
    """Pull every ``salt '*' <target> [args]`` invocation out of a docstring."""
    found = []
    for line in doc.splitlines():
        m = _SALT_LINE.match(line)
        if not m:
            continue
        target = m.group(1)
        args = m.group(2)
        found.append({"target": target, "args": args, "raw": line.strip()})
    return found


def _split_args(arg_str: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Split a CLI args string into positional + keyword tokens.

    Uses ``shlex`` so quoted values stay intact. Tokens of the form ``k=v`` go
    into keyword; everything else into positional. Order within each group is
    preserved.
    """
    if not arg_str.strip():
        return [], []
    try:
        tokens = shlex.split(arg_str)
    except ValueError:
        # Unbalanced quotes etc. — fall back to whitespace split.
        tokens = arg_str.split()
    positional: list[str] = []
    keyword: list[tuple[str, str]] = []
    for tok in tokens:
        kw = _KW.match(tok)
        if kw:
            keyword.append((kw.group("k"), kw.group("v")))
        else:
            positional.append(tok)
    return positional, keyword


def collect_all_examples() -> list[DocExample]:
    """Walk every module in ``saltext.vmware.modules`` and collect examples."""
    out: list[DocExample] = []
    for info in pkgutil.iter_modules(_modules_pkg.__path__):
        if info.ispkg:
            continue
        try:
            mod = importlib.import_module(f"saltext.vmware.modules.{info.name}")
        except ImportError:
            continue
        out.extend(_iter_doc_examples_from_module(mod))
    return out


def resolve_callable(example: DocExample) -> Callable | None:
    """Return the actual function object referenced by *example*, or None."""
    # The docstring uses __virtualname__, but the import path is the file name.
    # In our codebase __virtualname__ matches the file basename, so resolve via
    # the file path first; otherwise scan modules by virtualname.
    target_name = example.virtual_name
    try:
        mod = importlib.import_module(f"saltext.vmware.modules.{target_name}")
        return getattr(mod, example.func_name, None)
    except ImportError:
        pass
    for info in pkgutil.iter_modules(_modules_pkg.__path__):
        if info.ispkg:
            continue
        try:
            mod = importlib.import_module(f"saltext.vmware.modules.{info.name}")
        except ImportError:
            continue
        if getattr(mod, "__virtualname__", None) == target_name:
            return getattr(mod, example.func_name, None)
    return None


def signature_accepts(example: DocExample, func: Callable) -> tuple[bool, str]:
    """Check the function signature can be called with the example's args.

    Returns ``(ok, reason)``. ``reason`` is empty on success.
    """
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError) as exc:
        return False, f"no signature: {exc}"
    args = list(example.positional)
    kwargs = dict(example.keyword)
    try:
        sig.bind_partial(*args, **kwargs)
    except TypeError as exc:
        return False, str(exc)
    return True, ""
