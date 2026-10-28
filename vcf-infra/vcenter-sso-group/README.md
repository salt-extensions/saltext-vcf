# Local vCenter SSO group

This SLS uses `vcf_vcenter_sso_group.present` and the appliance's supported
`dir-cli ssogroup create` / `dir-cli group list --name` commands. It no longer
calls `/api/vcenter/identity/groups`, which returned route-level 404 on the
tested vCenter 9 appliance. No TLS/SSL change is required.

## Connection setup

The minion needs Paramiko, access to port 22, and an appliance account with
Bash as its SSH command shell and permission to run dir-cli (typically root).
Keep the existing vCenter SSO administrator credentials. Add SSH credentials
to the **same** `saltext.vcf.vcenter` configuration, through a protected pillar
or minion configuration; do not commit passwords:

```yaml
saltext.vcf:
  vcenter:
    host: mgmt-vc.vcf.nimbus.internal
    username: administrator@vsphere.local
    password: <SSO password supplied securely>
    ssh:
      username: root
      password: <appliance root password supplied securely>
      known_hosts: /etc/salt/vcenter_known_hosts
```

The optional SSH `host` defaults to the vCenter host; `port` defaults to 22.
The known-hosts file must exist **inside the minion container** and contain a
trusted key for that exact host/IP. Verify its fingerprint against the
appliance before installing it; unknown or changed keys are rejected.
System known-hosts files are also loaded. Named connection profiles follow
`saltext.vcf.profiles.<profile>.vcenter` with the same structure.

The SSO password is sent to dir-cli's stdin prompt, not put in command
arguments or log messages. The local domain is checked with `vmafd-cli` before
lookup or creation. Only explicit dir-cli error 1319 means a missing group;
authentication errors and unavailable commands fail the state.

## Apply and verify

```sh
salt '5ba0c302-d625-4a47-8c83-aff2f9629766' state.apply \
  vcenter-sso-group.vcenter-sso-group saltenv=sse test=True
salt '5ba0c302-d625-4a47-8c83-aff2f9629766' state.apply \
  vcenter-sso-group.vcenter-sso-group saltenv=sse test=False
```

Deploy the rebuilt extension image and updated SLS before testing. Preview
performs authenticated reads but never creates a group. Apply verifies the
group after creation; a second apply should report `already exists` with no
changes. Existing descriptions and memberships are not reconciled.

In vSphere Client, check Administration > Single Sign On > Users and Groups >
Groups, select `vsphere.local`, and search for `vcf-automation-operators`.
Alternatively, from appliance Bash (prompts for SSO password):

```sh
/usr/lib/vmware-vmafd/bin/dir-cli group list \
  --name vcf-automation-operators --login administrator@vsphere.local
```

An empty group may list no members: the command's successful exit status is
the presence check. This control neither adds members nor assigns permissions.
The older REST group/user execution functions are unchanged; this SLS no
longer uses them.

References: Broadcom KB [323563](https://knowledge.broadcom.com/external/article/323563)
(group creation) and [401445](https://knowledge.broadcom.com/external/article/401445)
(missing-group diagnostic). Live creation still needs validation on the target
appliance after deployment; unit tests mock the SSH transport.
