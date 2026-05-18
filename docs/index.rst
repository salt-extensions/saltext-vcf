``saltext-vcf``: Salt for VMware Cloud Foundation
=====================================================

Salt extension for VCF 9.x. Covers vCenter, NSX, SDDC Manager, VCF
Operations, VKS, VMSP, and vSAN.

Coverage
--------

* **vCenter** — clusters, hosts, VMs, datacenters, datastores, networks,
  storage policies, content libraries, folders, resource pools, tags,
  VM snapshots, custom attributes, appliance services, KMS providers,
  Cluster Configuration Profile (vSphere 9), Supervisor services, VM
  classes, namespaces.
* **NSX** — Policy API (segments, tier-0/tier-1, groups, security
  policies, firewall rules, services, context profiles, NAT, IP
  blocks/pools, DHCP, edge clusters) and Management API (node, cluster
  status, transport zones/nodes, compute collections, RBAC).
* **SDDC Manager** — hosts, clusters, workload domains, vCenters,
  bundles, network pools, releases, upgrades, certificates, credential
  rotation, VMSP service health via ``/v1/vcf-services``.
* **VCF Operations** — resources, adapters, alert/symptom definitions,
  active alerts, policies, notifications, recommendations, RBAC,
  collectors, credentials, super metrics, resource groups, reports,
  maintenance schedules, tasks, solutions, node status.
* **VKS** — Supervisor enablement, namespaces, services catalog, VM
  classes, software lifecycle, compatibility probes, kubeconfig fetch,
  ``saltext-kubernetes`` bridge.
* **vSAN** — cluster config, disk groups, fault domains, health
  (pyVmomi SOAP).

Quickstart
----------

.. code-block:: bash

   pip install saltext.vcf

.. code-block:: yaml

   saltext.vcf:
     vcenter:
       host: mgmt-vc.example.com
       username: administrator@vsphere.local
       password: secret
       verify_ssl: false

.. code-block:: bash

   salt-call vcf_vcenter_cluster.list_
   salt-call vcf_vcfops_resource.list_ page_size=10
   salt-call vcf_sddc_domain.list_

See :doc:`topics/configuration` for the full pillar shape.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   topics/installation
   topics/configuration
   topics/resources-framework
   topics/vks-bridge
   topics/vsan-soap
   topics/vmsp-mediated

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 2
   :caption: Reference

   ref/modules/index
   ref/states/index
   ref/resources/index
   ref/clients/index
   ref/utils/index
   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
