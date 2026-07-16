"""Execution module for SDDC Manager software bundles."""

from saltext.vcf.clients import sddc_bundles as c

__virtualname__ = "vcf_sddc_bundles"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.list_

    """
    return c.list_(__opts__, profile=profile)


def get(bundle_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.get <bundle_id>

    """
    return c.get(__opts__, bundle_id, profile=profile)


def download(bundle_id, profile=None):
    """Download.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.download <bundle_id>

    """
    return c.download(__opts__, bundle_id, profile=profile)


def upload(bundle_file_path, manifest_file_path, signature_file_path, profile=None):
    """Register an offline patch bundle already staged on SDDC Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.upload \\
            /nfs/vmware/vcf/nfs-mount/apToolBundles/bundle.tar \\
            /nfs/vmware/vcf/nfs-mount/apToolBundles/bundle.manifest \\
            /nfs/vmware/vcf/nfs-mount/apToolBundles/bundle.sig

    """
    return c.upload(
        __opts__,
        bundle_file_path,
        manifest_file_path,
        signature_file_path,
        profile=profile,
    )


def delete(bundle_id, profile=None):
    """Delete a bundle from the LCM repository.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.delete <bundle_id>

    """
    return c.delete(__opts__, bundle_id, profile=profile)


def for_skip_upgrade(domain_id, profile=None):
    """List bundles applicable to a skip-upgrade of the given domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_bundles.for_skip_upgrade <domain_id>

    """
    return c.for_skip_upgrade(__opts__, domain_id, profile=profile)
