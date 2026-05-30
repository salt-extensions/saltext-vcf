from saltext.vcf.clients import automation_topology


def test_normalize_reference_pillar_to_native_shape():
    pillar = {
        "vcf_automation": {
            "connections": {
                "vcf_installer": {"host": "installer.test", "username": "admin"},
                "sddc_manager": {"host": "sddc.test"},
                "vcenter": {"host": "vc.test"},
                "nsxt": {"host": "nsx.test"},
            },
            "topology": {
                "vcf_installer": {
                    "installer_host": "installer.test",
                    "installer_ova_url": "http://example/installer.ova",
                    "installer_deploy_esxi": "esx-1.test",
                    "installer_vm_name": "vcf-installer",
                    "esxi_hosts": [{"fqdn": "esx-1.test", "username": "root", "password": "pw"}],
                    "sddc_spec": {"sddcId": "vcf-1"},
                    "timeout_sec": 7200,
                },
                "sddc_manager": {"fqdn": "sddc.test"},
                "vcenter": {"fqdn": "vc.test"},
                "esxi_hosts": [{"fqdn": "esx-1.test"}],
                "nsxt": {"transport_zones": [{"name": "overlay-tz", "type": "OVERLAY"}]},
                "poc_validation": {"vm_name": "poc"},
            },
        }
    }

    result = automation_topology.normalize(pillar)

    assert result["vcf_installer"]["host"] == "installer.test"
    assert result["sddc_manager"]["host"] == "sddc.test"
    assert result["vcenter"]["host"] == "vc.test"
    assert result["nsx"]["host"] == "nsx.test"
    assert result["installer_appliance"]["deployment_backend"] == "ovftool"
    assert result["installer_appliance"]["installer_deploy_esxi"] == "esx-1.test"
    assert result["bringup_spec"] == {"sddcId": "vcf-1"}
    assert result["bringup_timeout"] == 7200
    assert result["nsxt_topology"]["transport_zones"][0]["name"] == "overlay-tz"


def test_normalize_preserves_existing_native_values():
    pillar = {
        "saltext.vcf": {"vcenter": {"host": "native-vc.test"}},
        "vcf_automation": {"connections": {"vcenter": {"host": "reference-vc.test"}}},
    }

    result = automation_topology.normalize(pillar)

    assert result["vcenter"]["host"] == "native-vc.test"
