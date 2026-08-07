"""Tests for clients.vcenter_storage_policy PBM-backed create/update/delete."""

from unittest.mock import MagicMock
from unittest.mock import patch

import responses

from saltext.vcf.clients import vcenter_storage_policy as c

CONSTRAINTS = [{"tags": {"cat1": ["gold"]}}, {"capabilities": {"VSAN.hostFailuresToTolerate": 1}}]


def _profile(profile_id, name, description, constraints_obj):
    p = MagicMock()
    p.profileId = profile_id
    p.name = name
    p.description = description
    p.constraints = constraints_obj
    return p


def _pm(profiles, query_ids=None):
    pm = MagicMock()
    pm.PbmQueryProfile.return_value = (
        query_ids if query_ids is not None else [p.profileId for p in profiles]
    )
    pm.PbmRetrieveContent.return_value = profiles
    return pm


def test_find_profile_by_name(opts):
    p = _profile("id-1", "my-policy", "desc", None)
    pm = _pm([p])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        result = c.get_by_name(opts, "my-policy")
    assert result["id"] == "id-1"
    assert result["description"] == "desc"


def test_get_by_name_missing_returns_none(opts):
    pm = _pm([], query_ids=[])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        assert c.get_by_name(opts, "nope") is None


def test_create_builds_spec_and_returns_id(opts):
    pm = MagicMock()
    new_id = MagicMock()
    new_id.uniqueId = "new-id-1"
    pm.PbmCreate.return_value = new_id
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        result = c.create(opts, "my-policy", CONSTRAINTS, description="desc")
    assert result == "new-id-1"
    spec = pm.PbmCreate.call_args.kwargs["createSpec"]
    assert spec.name == "my-policy"
    assert spec.description == "desc"
    assert len(spec.constraints.subProfiles) == 2


def test_update_calls_pbm_update(opts):
    p = _profile("id-1", "my-policy", "old desc", None)
    pm = _pm([p])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        c.update(opts, "my-policy", constraints=CONSTRAINTS, description="new desc")
    pm.PbmUpdate.assert_called_once()
    assert pm.PbmUpdate.call_args.kwargs["profileId"] == "id-1"


def test_update_missing_raises(opts):
    pm = _pm([], query_ids=[])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        try:
            c.update(opts, "nope", description="x")
        except LookupError:
            pass
        else:
            raise AssertionError("expected LookupError")


def test_delete_calls_pbm_delete(opts):
    p = _profile("id-1", "my-policy", "desc", None)
    pm = _pm([p])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        c.delete(opts, "my-policy")
    pm.PbmDelete.assert_called_once_with(profileId=["id-1"])


def test_default_policy_get_returns_unique_id(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore",
        json=[{"datastore": "datastore-12", "name": "vsanDatastore"}],
        status=200,
    )
    pm = MagicMock()
    spec = MagicMock()
    spec.uniqueId = "policy-id-1"
    pm.PbmQueryDefaultRequirementProfile.return_value = spec
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        result = c.default_policy_get(opts, "vsanDatastore")
    assert result == "policy-id-1"
    hub = pm.PbmQueryDefaultRequirementProfile.call_args.kwargs["hub"]
    assert hub.hubId == "datastore-12"
    assert hub.hubType == "Datastore"


def test_default_policy_set_resolves_policy_and_datastore(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore",
        json=[{"datastore": "datastore-12", "name": "vsanDatastore"}],
        status=200,
    )
    p = _profile("id-1", "raid0-vm-policy", "desc", None)
    pm = _pm([p])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        c.default_policy_set(opts, "vsanDatastore", "raid0-vm-policy")
    pm.PbmAssignDefaultRequirementProfile.assert_called_once()
    kwargs = pm.PbmAssignDefaultRequirementProfile.call_args.kwargs
    assert kwargs["profile"] == "id-1"
    assert kwargs["datastores"][0].hubId == "datastore-12"


def test_default_policy_set_missing_policy_raises(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore",
        json=[{"datastore": "datastore-12", "name": "vsanDatastore"}],
        status=200,
    )
    pm = _pm([], query_ids=[])
    with patch(
        "saltext.vcf.clients.vcenter_storage_policy.pbm_utils.profile_manager", return_value=pm
    ):
        try:
            c.default_policy_set(opts, "vsanDatastore", "nope")
        except LookupError:
            pass
        else:
            raise AssertionError("expected LookupError")


def test_to_subprofiles_roundtrips_with_from_subprofiles(opts):
    subprofiles = c._to_subprofiles(CONSTRAINTS)  # noqa: SLF001
    assert len(subprofiles) == 2

    fake_profile = MagicMock()
    # SubProfileCapabilityConstraints instance check is real, so build one.
    from pyVmomi import pbm

    real_constraints = pbm.profile.SubProfileCapabilityConstraints(subProfiles=subprofiles)
    fake_profile.constraints = real_constraints

    result = c._from_subprofiles(fake_profile)  # noqa: SLF001
    assert {"tags": {"cat1": ["gold"]}} in result
    assert {"capabilities": {"VSAN.hostFailuresToTolerate": 1}} in result
