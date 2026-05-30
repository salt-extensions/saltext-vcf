from saltext.vcf.clients import installer_topology


def _valid_spec():
    return {
        "installer_appliance": {
            "installer_host": "vcf-installer.example.test",
            "installer_ova_url": "http://example.test/vcf-installer.ova",
            "installer_vm_name": "vcf-installer",
            "installer_deploy_esxi": "esx-1.example.test",
            "deployment_backend": "ovftool",
            "datastore": "datastore1",
            "disk_provisioning": "thin",
            "esxi_hosts": [
                {"fqdn": "esx-1.example.test", "ip": "10.0.0.11"},
                {"fqdn": "esx-2.example.test", "ip": "10.0.0.12"},
                {"fqdn": "esx-3.example.test", "ip": "10.0.0.13"},
            ],
        },
        "bringup_spec": {
            "sddcId": "vcf-mgmt",
            "workflowType": "VCF",
            "dnsSpec": {"subdomain": "example.test", "nameservers": ["10.0.0.2"]},
            "hostSpecs": [
                {
                    "hostname": "esx-1",
                    "credentials": {"username": "root", "password": "password"},
                },
                {
                    "hostname": "esx-2",
                    "credentials": {"username": "root", "password": "password"},
                },
                {
                    "hostname": "esx-3",
                    "credentials": {"username": "root", "password": "password"},
                },
            ],
            "sddcManagerSpec": {"hostname": "sddc-manager"},
            "vcenterSpec": {"hostname": "vcenter"},
            "nsxtSpec": {"hostname": "nsx"},
            "datastoreSpec": {"vsanSpec": {}},
            "clusterSpec": {"clusterName": "mgmt-cluster"},
            "networkSpecs": [
                {"networkType": "MANAGEMENT"},
                {"networkType": "VMOTION"},
                {"networkType": "VSAN"},
            ],
        },
    }


def test_validate_accepts_complete_standalone_installer_shape():
    result = installer_topology.validate(_valid_spec())

    assert result == {"valid": True, "errors": [], "warnings": []}


def test_validate_rejects_missing_required_wiring():
    spec = _valid_spec()
    spec["installer_appliance"]["installer_deploy_esxi"] = "unknown.example.test"
    spec["bringup_spec"]["hostSpecs"] = spec["bringup_spec"]["hostSpecs"][:2]
    spec["bringup_spec"]["networkSpecs"] = [{"networkType": "MANAGEMENT"}]

    result = installer_topology.validate(spec)

    assert result["valid"] is False
    assert any("installer_deploy_esxi" in error for error in result["errors"])
    assert any("at least three ESXi hosts" in error for error in result["errors"])
    assert any("VMOTION" in error for error in result["errors"])
    assert any("VSAN" in error for error in result["errors"])


def test_validate_warns_for_ovftool_without_standalone_storage_defaults():
    spec = _valid_spec()
    spec["installer_appliance"].pop("datastore")
    spec["installer_appliance"]["disk_provisioning"] = "thick"

    result = installer_topology.validate(spec)

    assert result["valid"] is True
    assert any("datastore" in warning for warning in result["warnings"])
    assert any("disk_provisioning: thin" in warning for warning in result["warnings"])
