"""Execution module for SDDC Manager cluster personalities."""

from saltext.vcf.clients import sddc_personalities as c

__virtualname__ = "vcf_sddc_personalities"


def __virtual__():
    return __virtualname__


def list_(personality_name=None, cluster_id=None, profile=None):
    """List personalities, optionally filtered.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.list_
        salt '*' vcf_sddc_personalities.list_ personality_name=cluster-image-8.0u3

    """
    return c.list_(
        __opts__,
        personality_name=personality_name,
        cluster_id=cluster_id,
        profile=profile,
    )


def get(personality_id, profile=None):
    """Get a personality by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.get <personality_id>

    """
    return c.get(__opts__, personality_id, profile=profile)


def create(personality_spec, profile=None):
    """Import a new personality.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.create \\
            '{"personalityName": "cluster-image-8.0u3", "fileId": "abc123"}'

    """
    return c.create(__opts__, personality_spec, profile=profile)


def delete(personality_id, profile=None):
    """Delete a personality.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.delete <personality_id>

    """
    return c.delete(__opts__, personality_id, profile=profile)


def rename(personality_id, personality_name, profile=None):
    """Rename a personality.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.rename <personality_id> <new_name>

    """
    return c.rename(__opts__, personality_id, personality_name, profile=profile)


def upload_files(upload_spec, profile=None):
    """Upload the files that back a personality.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_personalities.upload_files \\
            '{"filePath": "/nfs/.../personality.zip", "personalityName": "..."}'

    """
    return c.upload_files(__opts__, upload_spec, profile=profile)
