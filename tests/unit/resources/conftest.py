"""Fixtures for testing the Salt Resources framework integration."""

import pytest


@pytest.fixture
def resources_pillar():
    """Pillar shaped as the Salt Resources framework expects."""
    return {
        "resources": {
            "vcenter": {
                "instances": {
                    "mgmt-vc": {
                        "host": "vc.test",
                        "username": "u",
                        "password": "p",
                        "verify_ssl": False,
                    },
                    "prod-vc": {
                        "host": "prod-vc.test",
                        "username": "u",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "sddc": {
                "instances": {
                    "sddc-01": {
                        "host": "sm.test",
                        "username": "u",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "nsx": {
                "instances": {
                    "mgmt-nsx": {
                        "host": "nsx.test",
                        "username": "u",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "esxi": {
                "instances": {
                    "esxi-01": {
                        "host": "esxi.test",
                        "username": "root",
                        "password": "p",
                        "verify_ssl": False,
                    },
                    "esxi-02": {
                        "host": "esxi02.test",
                        "username": "root",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "vcf_ops": {
                "instances": {
                    "ops-prod": {
                        "host": "ops.test",
                        "username": "admin",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "vmsp": {
                "instances": {
                    "vcf-vmsp": {
                        "host": "vmsp.test",
                        "username": "admin@vsp.local",
                        "password": "p",
                        "verify_ssl": False,
                    },
                },
            },
            "vcf_vm": {
                "instances": {
                    "web-01": {
                        "vcenter": "mgmt-vc",
                        "moid": "vm-100",
                        "labels": {"tier": "production", "app": "web"},
                    },
                    "web-02": {
                        "vcenter": "mgmt-vc",
                        "moid": "vm-101",
                        "labels": {"tier": "production"},
                    },
                    "orphan": {
                        # references a vcenter id that doesn't exist — for error tests
                        "vcenter": "missing-vc",
                        "moid": "vm-999",
                    },
                },
            },
        },
    }


@pytest.fixture
def framework_opts(resources_pillar):
    return {"pillar": resources_pillar}


@pytest.fixture
def inject_resource_dunders(monkeypatch):
    """Set ``__resource__`` and ``__context__`` on a resource module.

    For the esxi resource type, pass ``vcenter_instances`` so the
    ``via_vcenter: "<id>"`` reference can be resolved.
    """

    def _inject(module, resource_id, context_key, instances, vcenter_instances=None):
        monkeypatch.setattr(module, "__resource__", {"id": resource_id}, raising=False)
        ctx_entry = {"initialized": True, "instances": instances}
        if vcenter_instances is not None:
            ctx_entry["vcenter_instances"] = vcenter_instances
        monkeypatch.setattr(
            module,
            "__context__",
            {context_key: ctx_entry},
            raising=False,
        )

    return _inject
