"""Tests for vcfa_iam and vcfa_custom_role."""

import json

import pytest
import responses

from saltext.vcf.clients import vcfa_custom_role
from saltext.vcf.clients import vcfa_iam

# -- iam ----------------------------------------------------------------


def test_iam_list_orgs(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/loggedin/user/orgs",
        json={"items": [{"id": "org-1", "displayName": "Org"}]},
        status=200,
    )
    out = vcfa_iam.list_orgs(opts)
    assert out == [{"id": "org-1", "displayName": "Org"}]


def test_iam_get_user_roles(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/users/u-1/roles",
        json={"organizationRoles": [], "serviceRoles": []},
        status=200,
    )
    out = vcfa_iam.get_user_roles(opts, "org-1", "u-1")
    assert out == {"organizationRoles": [], "serviceRoles": []}


def test_iam_patch_user_roles_add_and_remove(opts, vcfa_authed):
    vcfa_authed.add(
        responses.PATCH,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/users/u-1/roles",
        json={},
        status=200,
    )
    vcfa_iam.patch_user_roles(
        opts,
        "org-1",
        "u-1",
        add=[{"name": "org_owner", "resource": "org-1"}],
        remove=[{"name": "org_member", "resource": "org-1"}],
    )
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {
        "rolesToAdd": [{"name": "org_owner", "resource": "org-1"}],
        "rolesToRemove": [{"name": "org_member", "resource": "org-1"}],
    }


def test_iam_patch_user_roles_requires_either(opts):
    with pytest.raises(ValueError):
        vcfa_iam.patch_user_roles(opts, "org-1", "u-1")


# -- custom_role ------------------------------------------------------


def test_custom_role_list(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iam/api/roles",
        json={"items": [{"id": "r-1"}]},
        status=200,
    )
    out = vcfa_custom_role.list_(opts)
    assert out == [{"id": "r-1"}]


def test_custom_role_create_and_delete(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iam/api/roles",
        json={"id": "r-1"},
        status=200,
    )
    vcfa_custom_role.create(
        opts,
        {
            "name": "role-x",
            "displayName": "Role X",
            "rolePermissions": ["csp:org_owner"],
            "orgId": "org-1",
        },
    )

    vcfa_authed.add(responses.DELETE, "https://vcfa.test/iam/api/roles/r-1", status=204)
    assert vcfa_custom_role.delete(opts, "r-1") == {}
