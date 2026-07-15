"""Execution module for vLCM single-image software lifecycle on a cluster."""

from saltext.vcf.clients import cluster_config_software as c

__virtualname__ = "vcf_cluster_config_software"


def __virtual__():
    return __virtualname__


def get(cluster, profile=None):
    """Return the cluster's desired software image (or ``None``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config_software.get <cluster>
    """
    return c.get(__opts__, cluster, profile=profile)


def effective_components(cluster, profile=None):
    """Return the components currently in effect across the cluster."""
    return c.effective_components(__opts__, cluster, profile=profile)


def solutions(cluster, profile=None):
    """Return the registered solutions layered into the image."""
    return c.solutions(__opts__, cluster, profile=profile)


def drafts_list(cluster, profile=None):
    """List open drafts on the cluster."""
    return c.drafts_list(__opts__, cluster, profile=profile)


def draft_get(cluster, draft_id, profile=None):
    """Return one draft."""
    return c.draft_get(__opts__, cluster, draft_id, profile=profile)


def draft_create(cluster, profile=None):
    """Open a draft seeded from the desired image. Returns the draft id."""
    return c.draft_create(__opts__, cluster, profile=profile)


def draft_delete(cluster, draft_id, profile=None):
    """Delete a draft."""
    return c.draft_delete(__opts__, cluster, draft_id, profile=profile)


def draft_update_base_image(cluster, draft_id, version, profile=None):
    """Set the ESXi base-image version on a draft."""
    return c.draft_update_base_image(__opts__, cluster, draft_id, version, profile=profile)


def draft_set_add_on(cluster, draft_id, name, version, profile=None):
    """Pin a vendor add-on on a draft."""
    return c.draft_set_add_on(__opts__, cluster, draft_id, name, version, profile=profile)


def draft_remove_add_on(cluster, draft_id, profile=None):
    """Remove the add-on from a draft."""
    return c.draft_remove_add_on(__opts__, cluster, draft_id, profile=profile)


def draft_set_component(cluster, draft_id, component_name, version, profile=None):
    """Pin a component version on a draft."""
    return c.draft_set_component(
        __opts__, cluster, draft_id, component_name, version, profile=profile
    )


def draft_remove_component(cluster, draft_id, component_name, profile=None):
    """Remove a component from a draft."""
    return c.draft_remove_component(__opts__, cluster, draft_id, component_name, profile=profile)


def draft_set_hardware_support(cluster, draft_id, packages, profile=None):
    """Set firmware/hardware-support packages on a draft."""
    return c.draft_set_hardware_support(__opts__, cluster, draft_id, packages, profile=profile)


def draft_commit(cluster, draft_id, profile=None):
    """Commit a draft, making it the cluster's desired image."""
    return c.draft_commit(__opts__, cluster, draft_id, profile=profile)


def check(cluster, profile=None):
    """Run a pre-check. Returns a vCenter task id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config_software.check <cluster>
    """
    return c.check(__opts__, cluster, profile=profile)


def stage(cluster, hosts=None, profile=None):
    """Pre-stage payloads on hosts (optional ``hosts`` list)."""
    return c.stage(__opts__, cluster, hosts=hosts, profile=profile)


def apply(cluster, accept_eula=True, profile=None):
    """Apply the desired image. Returns a vCenter task id."""
    return c.apply(__opts__, cluster, accept_eula=accept_eula, profile=profile)


def scan(cluster, profile=None):
    """Run a compliance scan. Returns a vCenter task id."""
    return c.scan(__opts__, cluster, profile=profile)


def last_apply_result(cluster, profile=None):
    """Return the last apply result, or ``None``."""
    return c.last_apply_result(__opts__, cluster, profile=profile)


def last_check_result(cluster, profile=None):
    """Return the last check result, or ``None``."""
    return c.last_check_result(__opts__, cluster, profile=profile)


def last_compliance_result(cluster, profile=None):
    """Return the last compliance result, or ``None``."""
    return c.last_compliance_result(__opts__, cluster, profile=profile)


def last_stage_result(cluster, profile=None):
    """Return the last stage result, or ``None``."""
    return c.last_stage_result(__opts__, cluster, profile=profile)
