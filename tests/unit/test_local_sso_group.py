"""Focused tests; also runnable with stdlib unittest without Salt installed."""

import shlex
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.clients import vcenter_sso_group as client
from saltext.vcf.states import vcf_vcenter_sso_group as state
from saltext.vcf.utils import ssh


class LocalGroupTests(unittest.TestCase):
    def setUp(self):
        self.opts = {"saltext.vcf": {"vcenter": {
            "host": "vc.test", "username": "administrator@vsphere.local",
            "password": "test-only-sso-secret", "ssh": {
                "username": "root", "password": "test-only-root-secret",
                "known_hosts": "/trusted/hosts"}}}, "test": False}
        self.domain = (0, "vsphere.local\n", "")
        self.missing = (39, "", "dir-cli failed. Error 1319: ERROR_NO_SUCH_GROUP (1319)")
        self.ok = (0, "", "")
        self.run = patch.object(client.ssh, "run").start()
        self.addCleanup(patch.stopall)
        state.__opts__ = self.opts

    def test_empty_group_exists(self):
        self.run.side_effect = [self.domain, self.ok]
        self.assertEqual(client.get_or_none(self.opts, "Ops", "vsphere.local"),
                         {"name": "Ops", "domain": "vsphere.local"})

    def test_only_missing_group_is_absent(self):
        self.run.side_effect = [self.domain, self.missing]
        self.assertIsNone(client.get_or_none(self.opts, "Ops", "vsphere.local"))

    def test_auth_failure_does_not_create(self):
        self.run.side_effect = [self.domain, (1, "", "dir-cli failed. Error 1326: login failed")]
        ret = state.present("Ops", "vsphere.local")
        self.assertFalse(ret["result"])
        self.assertEqual(ret["changes"], {})
        self.assertEqual(self.run.call_count, 2)

    def test_unknown_failure_not_absence(self):
        self.run.side_effect = [self.domain, (127, "", "command not found")]
        with self.assertRaises(RuntimeError):
            client.get_or_none(self.opts, "Ops", "vsphere.local")

    def test_wrong_domain_never_creates(self):
        self.run.return_value = self.domain
        with self.assertRaises(ValueError):
            client.create(self.opts, "Ops", "external.test")
        self.assertEqual(self.run.call_count, 1)

    def test_shell_quoting_and_password_stdin(self):
        self.run.side_effect = [self.domain, self.ok, self.ok]
        name = "Ops'; echo nope"
        desc = "Owner's test; $(whoami)"
        client.create(self.opts, name, "vsphere.local", desc)
        call = self.run.call_args_list[1]
        args = shlex.split(call.args[1])
        self.assertEqual(args[args.index("--name") + 1], name)
        self.assertEqual(args[args.index("--description") + 1], desc)
        self.assertNotIn("--password", args)
        self.assertNotIn("test-only-sso-secret", call.args[1])
        self.assertEqual(call.kwargs["input_data"], "test-only-sso-secret\n")
        self.assertTrue(call.args[0]["verify_host_key"])
        self.assertEqual(call.args[0]["host"], "vc.test")

    def test_successful_apply_and_repeat(self):
        self.run.side_effect = [self.domain, self.missing, self.domain, self.ok,
                                self.ok, self.domain, self.ok]
        ret = state.present("Ops", "vsphere.local")
        self.assertTrue(ret["result"])
        self.assertEqual(ret["changes"]["new"]["name"], "Ops")
        ret = state.present("Ops", "vsphere.local")
        self.assertTrue(ret["result"])
        self.assertEqual(ret["changes"], {})

    def test_preview_never_writes(self):
        self.opts["test"] = True
        self.run.side_effect = [self.domain, self.missing]
        self.assertIsNone(state.present("Ops", "vsphere.local")["result"])
        self.assertEqual(self.run.call_count, 2)

    def test_creation_must_be_verified(self):
        self.run.side_effect = [self.domain, self.ok, self.missing]
        with self.assertRaisesRegex(RuntimeError, "not found on verification"):
            client.create(self.opts, "Ops", "vsphere.local")

    def test_failed_creation_redacts_output(self):
        self.run.side_effect = [self.domain, (1, "test-only-sso-secret", "failed")]
        with self.assertRaises(RuntimeError) as exc:
            client.create(self.opts, "Ops", "vsphere.local")
        self.assertNotIn("test-only-sso-secret", str(exc.exception))

    def test_missing_credentials_fails_before_ssh(self):
        self.opts["saltext.vcf"]["vcenter"].pop("ssh")
        self.assertFalse(state.present("Ops", "vsphere.local")["result"])
        self.run.assert_not_called()

    def test_multiline_password_rejected(self):
        self.opts["saltext.vcf"]["vcenter"]["password"] = "one\ntwo"
        self.assertFalse(state.present("Ops", "vsphere.local")["result"])
        self.run.assert_not_called()

    def test_pillar_and_profile(self):
        config = self.opts.pop("saltext.vcf")
        self.opts["pillar"] = {"saltext.vcf": {"profiles": {"vc": config}}}
        self.run.side_effect = [self.domain, self.ok]
        client.get_or_none(self.opts, "Ops", "VSPHERE.LOCAL", profile="vc")
        self.assertEqual(self.run.call_args.args[0]["host"], "vc.test")


class SshInputTests(unittest.TestCase):
    def test_stdin_and_host_key_verification(self):
        paramiko = MagicMock()
        session = paramiko.SSHClient.return_value
        stdin, stdout, stderr = MagicMock(), MagicMock(), MagicMock()
        session.exec_command.return_value = (stdin, stdout, stderr)
        stdout.read.return_value = b"ok"
        stderr.read.return_value = b""
        stdout.channel.recv_exit_status.return_value = 0
        with patch.dict("sys.modules", {"paramiko": paramiko}):
            result = ssh.run({"host": "vc", "verify_host_key": True,
                              "known_hosts": "/trusted/hosts"}, "dir-cli", input_data="secret\n")
        self.assertEqual(result, (0, "ok", ""))
        session.load_system_host_keys.assert_called_once()
        session.load_host_keys.assert_called_once_with("/trusted/hosts")
        session.set_missing_host_key_policy.assert_called_once_with(paramiko.RejectPolicy.return_value)
        stdin.write.assert_called_once_with("secret\n")
        stdin.channel.shutdown_write.assert_called_once()
        session.exec_command.assert_called_once_with("dir-cli", timeout=30)
        session.close.assert_called_once()

    def test_legacy_no_stdin_and_connection_failure_cleanup(self):
        paramiko = MagicMock()
        session = paramiko.SSHClient.return_value
        session.connect.side_effect = OSError("connection refused")
        with patch.dict("sys.modules", {"paramiko": paramiko}):
            with self.assertRaises(RuntimeError):
                ssh.run({"host": "vc"}, "read-only-command")
        session.close.assert_called_once()
        session.exec_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
