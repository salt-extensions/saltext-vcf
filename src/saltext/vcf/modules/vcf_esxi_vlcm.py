"""Execution module for vCenter's ESX Lifecycle Manager (vLCM) REST API.

Patches ESXi hosts in a vSphere cluster: configure/sync depots, define a
desired image, set the cluster's apply policy, then scan/precheck/stage/
remediate against it. See :mod:`saltext.vcf.clients.esxi_vlcm` for the
underlying REST calls, and :mod:`saltext.vcf.states.vcf_esxi_vlcm` for the
declarative/idempotent workflow.

Quick reference::

    # Depots
    salt-call vcf_esxi_vlcm.online_depot_list
    salt-call vcf_esxi_vlcm.offline_depot_create '{"location": "http://repo/depot.zip"}'
    salt-call vcf_esxi_vlcm.depot_sync

    # Desired image
    salt-call vcf_esxi_vlcm.desired_image_get domain-c9
    salt-call vcf_esxi_vlcm.draft_import_software_spec domain-c9 '{"base_image": {"version": "9"}}'
    salt-call vcf_esxi_vlcm.draft_commit domain-c9 draft-1

    # Lifecycle
    salt-call vcf_esxi_vlcm.compliance_scan domain-c9
    salt-call vcf_esxi_vlcm.remediate domain-c9
"""

from saltext.vcf.clients import esxi_vlcm as c

__virtualname__ = "vcf_esxi_vlcm"


def __virtual__():
    return __virtualname__


def online_depot_list(profile=None):
    """Online depot list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.online_depot_list

    """
    return c.online_depot_list(__opts__, profile=profile)


def online_depot_create(body, profile=None):
    """Online depot create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.online_depot_create <body>

    """
    return c.online_depot_create(__opts__, body, profile=profile)


def online_depot_update(depot_id, body, profile=None):
    """Online depot update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.online_depot_update <depot_id> <body>

    """
    return c.online_depot_update(__opts__, depot_id, body, profile=profile)


def offline_depot_list(profile=None):
    """Offline depot list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.offline_depot_list

    """
    return c.offline_depot_list(__opts__, profile=profile)


def offline_depot_get(depot_id, profile=None):
    """Offline depot get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.offline_depot_get <depot_id>

    """
    return c.offline_depot_get(__opts__, depot_id, profile=profile)


def offline_depot_create(body, profile=None):
    """Offline depot create (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.offline_depot_create <body>

    """
    return c.offline_depot_create(__opts__, body, profile=profile)


def offline_depot_delete(depot_id, profile=None):
    """Offline depot delete (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.offline_depot_delete <depot_id>

    """
    return c.offline_depot_delete(__opts__, depot_id, profile=profile)


def depot_sync(profile=None):
    """Depot sync (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.depot_sync

    """
    return c.depot_sync(__opts__, profile=profile)


def desired_image_get(cluster, profile=None):
    """Desired image get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.desired_image_get <cluster>

    """
    return c.desired_image_get(__opts__, cluster, profile=profile)


def base_image_get(cluster, profile=None):
    """Base image get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.base_image_get <cluster>

    """
    return c.base_image_get(__opts__, cluster, profile=profile)


def drafts_list(cluster, profile=None):
    """Drafts list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.drafts_list <cluster>

    """
    return c.drafts_list(__opts__, cluster, profile=profile)


def draft_get(cluster, draft_id, profile=None):
    """Draft get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.draft_get <cluster> <draft_id>

    """
    return c.draft_get(__opts__, cluster, draft_id, profile=profile)


def draft_delete(cluster, draft_id, profile=None):
    """Draft delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.draft_delete <cluster> <draft_id>

    """
    return c.draft_delete(__opts__, cluster, draft_id, profile=profile)


def draft_import_software_spec(cluster, image_spec, profile=None):
    """Draft import software spec (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.draft_import_software_spec <cluster> <image_spec>

    """
    return c.draft_import_software_spec(__opts__, cluster, image_spec, profile=profile)


def draft_validate(cluster, draft_id, profile=None):
    """Draft validate (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.draft_validate <cluster> <draft_id>

    """
    return c.draft_validate(__opts__, cluster, draft_id, profile=profile)


def draft_commit(cluster, draft_id, message=None, profile=None):
    """Draft commit (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.draft_commit <cluster> <draft_id>

    """
    return c.draft_commit(__opts__, cluster, draft_id, message=message, profile=profile)


def apply_policy_get(cluster, profile=None):
    """Apply policy get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.apply_policy_get <cluster>

    """
    return c.apply_policy_get(__opts__, cluster, profile=profile)


def apply_policy_set(cluster, policy_spec, profile=None):
    """Apply policy set.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.apply_policy_set <cluster> <policy_spec>

    """
    return c.apply_policy_set(__opts__, cluster, policy_spec, profile=profile)


def compliance_scan(cluster, commit="1", hosts=None, profile=None):
    """Compliance scan (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.compliance_scan <cluster>

    """
    return c.compliance_scan(__opts__, cluster, commit=commit, hosts=hosts, profile=profile)


def precheck(cluster, commit="1", profile=None):
    """Precheck (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.precheck <cluster>

    """
    return c.precheck(__opts__, cluster, commit=commit, profile=profile)


def stage(cluster, commit="1", hosts=None, profile=None):
    """Stage (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.stage <cluster>

    """
    return c.stage(__opts__, cluster, commit=commit, hosts=hosts, profile=profile)


def remediate(cluster, accept_eula=True, profile=None):
    """Remediate (task).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.remediate <cluster>

    """
    return c.remediate(__opts__, cluster, accept_eula=accept_eula, profile=profile)


def last_check_result(cluster, profile=None):
    """Last check result.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.last_check_result <cluster>

    """
    return c.last_check_result(__opts__, cluster, profile=profile)


def apply_impact_report(cluster, profile=None):
    """Apply impact report.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.apply_impact_report <cluster>

    """
    return c.apply_impact_report(__opts__, cluster, profile=profile)


def last_apply_result(cluster, profile=None):
    """Last apply result.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.last_apply_result <cluster>

    """
    return c.last_apply_result(__opts__, cluster, profile=profile)


def wait_for_task(resp, timeout=1800, poll_interval=10, profile=None):
    """Wait for task.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_vlcm.wait_for_task <resp>

    """
    return c.wait_for_task(
        __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
    )
