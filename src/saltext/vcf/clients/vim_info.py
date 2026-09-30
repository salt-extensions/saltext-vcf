"""vSphere ServiceInstance information (``ServiceContent.about``) via SOAP.

Port of ``vmware_vsphere.system_info``. Returns the ``aboutInfo`` of the
connected service (vCenter or standalone ESXi HostAgent) as a plain dict.
"""

from saltext.vcf.utils import vim as soap


def about(opts, profile=None):
    """Return the ServiceInstance ``about`` object as a plain dict.

    Keys include ``name``, ``fullName``, ``apiVersion``, ``apiType``,
    ``productLineId``, ``version``, ``build``, ``osType``, ``localeVersion``.
    ``apiType`` is ``HostAgent`` for a direct ESXi connection and
    ``VirtualCenter`` for vCenter.
    """
    si = soap.get_service_instance(opts, profile=profile)
    content = si.RetrieveContent()
    about = content.about
    out = {}
    for attrib in dir(about):
        if attrib.startswith("_"):
            continue
        val = getattr(about, attrib, None)
        if callable(val):
            continue
        out[attrib] = val
    return out
