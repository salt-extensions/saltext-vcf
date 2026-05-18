"""Execution module for datastore file transfer + manipulation."""

from saltext.vcf.clients import vim_datastore_file as c

__virtualname__ = "vcf_vim_datastore_file"


def __virtual__():
    return __virtualname__


def list_(datacenter, datastore, path="", profile=None):
    """List files under ``[datastore] path``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.list_ <datacenter> <datastore> <path>

    """
    return c.list_(__opts__, datacenter, datastore, path=path, profile=profile)


def mkdir(datacenter, datastore, path, create_parents=True, profile=None):
    """Create a directory on the datastore.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.mkdir <datacenter> <datastore> <path>

    """
    return c.mkdir(
        __opts__, datacenter, datastore, path, create_parents=create_parents, profile=profile
    )


def delete(datacenter, datastore, path, profile=None):
    """Delete a file or directory.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.delete <datacenter> <datastore> <path>

    """
    return c.delete(__opts__, datacenter, datastore, path, profile=profile)


def move(
    src_datacenter,
    src_datastore,
    src_path,
    dst_datacenter,
    dst_datastore,
    dst_path,
    force=False,
    profile=None,
):
    """Move a datastore file/folder.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.move <src_dc> <src_ds> <src_path> <dst_dc> <dst_ds> <dst_path>

    """
    return c.move(
        __opts__,
        src_datacenter,
        src_datastore,
        src_path,
        dst_datacenter,
        dst_datastore,
        dst_path,
        force=force,
        profile=profile,
    )


def upload(datacenter, datastore, local_path, ds_path, profile=None):
    """Upload a local file to ``[datastore] ds_path``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.upload <dc> <ds> <local_path> <ds_path>

    """
    return c.upload(__opts__, datacenter, datastore, local_path, ds_path, profile=profile)


def download(datacenter, datastore, ds_path, local_path, profile=None):
    """Download ``[datastore] ds_path`` to *local_path*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_file.download <dc> <ds> <ds_path> <local_path>

    """
    return c.download(__opts__, datacenter, datastore, ds_path, local_path, profile=profile)
