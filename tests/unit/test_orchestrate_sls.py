"""Smoke tests for the shipped _orchestrate/vcf_deploy SLS files.

Renders each SLS via Jinja+YAML and verifies that every state ID resolves
to a real ``saltext.vcf`` state function. Catches mismatched function
names without requiring a live Salt master.
"""

import importlib
from pathlib import Path

import jinja2
import pytest
import yaml

SLS_DIR = (
    Path(__file__).parent.parent.parent / "src" / "saltext" / "vcf" / "_orchestrate" / "vcf_deploy"
)
EXPECTED_SLS = ("full_stack.sls", "installer_appliance.sls", "bringup.sls")


def _render(path):
    """Render an SLS to a Python dict via Jinja2 + safe-yaml."""
    template = jinja2.Template(path.read_text(), undefined=jinja2.ChainableUndefined)
    rendered = template.render(pillar={"saltext.vcf": {}}, grains={}, opts={})
    return yaml.safe_load(rendered) or {}


def test_expected_sls_files_present():
    for name in EXPECTED_SLS:
        assert (SLS_DIR / name).is_file(), f"missing orchestrate SLS: {name}"


@pytest.mark.parametrize("name", EXPECTED_SLS)
def test_sls_renders(name):
    data = _render(SLS_DIR / name)
    assert isinstance(data, dict)


def _collect_state_calls(rendered):
    """Return list of (state_id, state_function) tuples for non-meta keys.

    Skips ``include:`` and ``extend:``. Each non-meta key maps to a dict
    whose first key is the state-function reference (e.g.,
    ``vcf_installer_appliance.running``).
    """
    out = []
    for state_id, body in rendered.items():
        if state_id in ("include", "extend"):
            continue
        if not isinstance(body, dict):
            continue
        for func_ref in body:
            out.append((state_id, func_ref))
    return out


def _resolve_state_function(func_ref):
    """Return the resolved callable for ``module.function`` from saltext.vcf.states."""
    module_name, _, fn_name = func_ref.partition(".")
    mod = importlib.import_module(f"saltext.vcf.states.{module_name}")
    fn = getattr(mod, fn_name, None)
    if fn is None or not callable(fn):
        raise AttributeError(f"{func_ref} not callable on {mod.__name__}")
    return fn


@pytest.mark.parametrize("name", EXPECTED_SLS)
def test_state_references_resolve(name):
    data = _render(SLS_DIR / name)
    calls = _collect_state_calls(data)
    if name == "full_stack.sls":
        # full_stack.sls is purely an aggregator (include:); no direct state calls.
        assert calls == []
        assert "include" in data
        return
    assert calls, f"{name} declares no state IDs"
    for _state_id, func_ref in calls:
        _resolve_state_function(func_ref)  # raises if missing


def test_full_stack_includes_both_stages():
    data = _render(SLS_DIR / "full_stack.sls")
    assert set(data.get("include", [])) == {
        "_orchestrate.vcf_deploy.installer_appliance",
        "_orchestrate.vcf_deploy.bringup",
    }


def test_bringup_requires_installer_appliance():
    data = _render(SLS_DIR / "bringup.sls")
    bringup = data["ensure_management_domain_bringup_complete"]
    args = bringup["vcf_installer_bringup.complete"]
    require_entries = next(
        item["require"] for item in args if isinstance(item, dict) and "require" in item
    )
    assert {"vcf_installer_appliance": "ensure_vcf_installer_appliance"} in require_entries
