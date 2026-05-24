"""Signature check for every ``CLI Example:`` in module docstrings.

For each parsed example, assert:
 1. The virtual module name resolves to a real saltext.vcf.modules.* file.
 2. The function exists on that module.
 3. The example's positional + keyword args can be bound to the function's signature.

Doesn't hit any network — pure introspection. The live invocation pass lives
in ``saltext-vcf-integration/test_doc_examples.py``.
"""

from __future__ import annotations

import pytest

from tests._doc_examples import collect_all_examples
from tests._doc_examples import resolve_callable
from tests._doc_examples import signature_accepts

_EXAMPLES = collect_all_examples()


@pytest.mark.parametrize(
    "example",
    _EXAMPLES,
    ids=[f"{e.virtual_name}.{e.func_name}:{e.raw[:60]}" for e in _EXAMPLES],
)
def test_doc_example_signature(example):
    func = resolve_callable(example)
    assert func is not None, (
        f"{example.virtual_name}.{example.func_name} (from {example.source_file}): "
        f"function not found — example line was: {example.raw}"
    )
    ok, reason = signature_accepts(example, func)
    assert ok, (
        f"{example.virtual_name}.{example.func_name} (from {example.source_file}): "
        f"signature rejects example args — {reason}; line: {example.raw}"
    )


def test_examples_collected():
    """Sanity: we found a non-trivial number of examples to test."""
    assert len(_EXAMPLES) > 50
