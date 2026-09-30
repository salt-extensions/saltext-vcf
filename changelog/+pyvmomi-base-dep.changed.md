``pyvmomi`` is now a base dependency (the whole SOAP surface —
``vcf_vim_*``, ``vcf_esxi_*``, ``vcf_vcenter_*`` REST+SOAP — loads with
a plain ``pip install saltext.vcf``). The ``[esxi]`` and ``[vcenter]``
extras now only add their remaining product deps (``pywbem`` /
``vmware-vcenter``); the ``[installer]`` extra is kept as a no-op
marker for backward compatibility.
