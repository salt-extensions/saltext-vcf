"""Tests for clients.vim_role and clients.vim_permission (SOAP via AuthorizationManager)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vmware.clients import vim_permission
from saltext.vmware.clients import vim_role


def _role(role_id, name, system, privileges):
    role = MagicMock()
    role.roleId = role_id
    role.name = name
    role.system = system
    role.info.label = name
    role.info.summary = f"{name} role"
    role.privilege = privileges
    return role


def _mgr(roles):
    mgr = MagicMock()
    mgr.roleList = roles
    return mgr


# ---------- vim_role ----------


def test_role_list_shape(opts):
    mgr = _mgr(
        [
            _role(1, "Admin", True, ["System.Anonymous", "System.Read", "System.View"]),
            _role(123, "MyRole", False, ["System.View"]),
        ]
    )
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        result = vim_role.list_(opts)
    assert {r["name"] for r in result} == {"Admin", "MyRole"}
    admin = next(r for r in result if r["name"] == "Admin")
    assert admin["system"] is True
    assert "System.Read" in admin["privilege"]


def test_role_get_found(opts):
    mgr = _mgr([_role(7, "MyRole", False, ["System.View"])])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        result = vim_role.get(opts, "MyRole")
    assert result["role_id"] == 7
    assert result["system"] is False


def test_role_get_missing_raises(opts):
    mgr = _mgr([])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        with pytest.raises(LookupError):
            vim_role.get(opts, "Nope")


def test_role_get_or_none(opts):
    mgr = _mgr([])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        assert vim_role.get_or_none(opts, "Nope") is None


def test_role_create_returns_new_id(opts):
    mgr = MagicMock()
    mgr.AddAuthorizationRole.return_value = 99
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        new_id = vim_role.create(opts, "MyRole", ["System.View"])
    assert new_id == 99
    mgr.AddAuthorizationRole.assert_called_once_with(name="MyRole", privIds=["System.View"])


def test_role_update_replaces_privileges(opts):
    mgr = _mgr([_role(7, "MyRole", False, ["System.View"])])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        vim_role.update(opts, "MyRole", ["System.View", "System.Read"])
    mgr.UpdateAuthorizationRole.assert_called_once_with(
        roleId=7, newName="MyRole", privIds=["System.View", "System.Read"]
    )


def test_role_rename_preserves_privileges(opts):
    mgr = _mgr([_role(7, "OldName", False, ["System.View"])])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        vim_role.rename(opts, "OldName", "NewName")
    mgr.UpdateAuthorizationRole.assert_called_once_with(
        roleId=7, newName="NewName", privIds=["System.View"]
    )


def test_role_delete_forwards_fail_if_used(opts):
    mgr = _mgr([_role(7, "MyRole", False, [])])
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        vim_role.delete(opts, "MyRole", fail_if_used=False)
    mgr.RemoveAuthorizationRole.assert_called_once_with(roleId=7, failIfUsed=False)


def test_role_list_privileges(opts):
    priv = MagicMock()
    priv.privId = "System.View"
    priv.name = "View"
    priv.privGroupName = "System"
    priv.onParent = False
    mgr = MagicMock()
    mgr.privilegeList = [priv]
    with patch("saltext.vmware.clients.vim_role.soap.authorization_manager", return_value=mgr):
        out = vim_role.list_privileges(opts)
    assert out == [{"id": "System.View", "name": "View", "group": "System", "on_parent": False}]


# ---------- vim_permission ----------


def _perm(moid, principal, role_id, propagate=True, group=False):
    p = MagicMock()
    p.entity._moId = moid
    p.principal = principal
    p.group = group
    p.roleId = role_id
    p.propagate = propagate
    return p


def test_permission_list_attaches_role_name(opts):
    mgr = MagicMock()
    mgr.roleList = [_role(7, "Admin", True, [])]
    mgr.RetrieveEntityPermissions.return_value = [_perm("vm-100", "alice@vsphere.local", 7)]
    entity = MagicMock()
    entity._moId = "vm-100"
    with patch(
        "saltext.vmware.clients.vim_permission.soap.authorization_manager", return_value=mgr
    ):
        with patch("saltext.vmware.clients.vim_permission._resolve_entity", return_value=entity):
            result = vim_permission.list_(opts, "vm-100")
    assert result[0]["role"] == "Admin"
    assert result[0]["principal"] == "alice@vsphere.local"


def test_permission_set_builds_permission_object(opts):
    mgr = MagicMock()
    mgr.roleList = [_role(7, "Admin", True, [])]
    entity = MagicMock()
    captured = {}

    def fake_permission_ctor(**kwargs):
        captured.update(kwargs)
        return MagicMock(**kwargs)

    with patch(
        "saltext.vmware.clients.vim_permission.soap.authorization_manager", return_value=mgr
    ):
        with patch("saltext.vmware.clients.vim_permission._resolve_entity", return_value=entity):
            with patch(
                "saltext.vmware.clients.vim_permission.vim.AuthorizationManager.Permission",
                side_effect=fake_permission_ctor,
            ):
                vim_permission.set_(opts, "vm-100", "alice@vsphere.local", "Admin")
    mgr.SetEntityPermissions.assert_called_once()
    assert captured["principal"] == "alice@vsphere.local"
    assert captured["roleId"] == 7
    assert captured["propagate"] is True


def test_permission_set_unknown_role_raises(opts):
    mgr = MagicMock()
    mgr.roleList = []
    with patch(
        "saltext.vmware.clients.vim_permission.soap.authorization_manager", return_value=mgr
    ):
        with patch(
            "saltext.vmware.clients.vim_permission._resolve_entity", return_value=MagicMock()
        ):
            with pytest.raises(LookupError, match="role 'Admin' not found"):
                vim_permission.set_(opts, "vm-100", "alice@vsphere.local", "Admin")


def test_permission_remove(opts):
    mgr = MagicMock()
    entity = MagicMock()
    with patch(
        "saltext.vmware.clients.vim_permission.soap.authorization_manager", return_value=mgr
    ):
        with patch("saltext.vmware.clients.vim_permission._resolve_entity", return_value=entity):
            vim_permission.remove(opts, "vm-100", "alice@vsphere.local")
    mgr.RemoveEntityPermission.assert_called_once_with(
        entity=entity, user="alice@vsphere.local", isGroup=False
    )


def test_permission_reset(opts):
    mgr = MagicMock()
    entity = MagicMock()
    with patch(
        "saltext.vmware.clients.vim_permission.soap.authorization_manager", return_value=mgr
    ):
        with patch("saltext.vmware.clients.vim_permission._resolve_entity", return_value=entity):
            vim_permission.reset(opts, "vm-100")
    mgr.ResetEntityPermissions.assert_called_once_with(entity=entity, permission=[])
