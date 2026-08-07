{% from "cluster-vsan-file-service/map.jinja" import cfg with context %}

cluster-vsan-file-service:
  vcf_vsan_file_service.configured:
    - cluster: {{ cfg.cluster.name }}
    - network_name: {{ cfg.file_service.network_name }}
    - domain_name: {{ cfg.file_service.domain_name }}
    - ip_to_fqdn: {{ cfg.file_service.ip_to_fqdn }}
    - subnet_mask: {{ cfg.file_service.subnet_mask }}
    - gateway_address: {{ cfg.file_service.gateway_address }}
    - dns_suffixes: {{ cfg.file_service.dns_suffixes }}
    - dns_address: {{ cfg.file_service.dns_address }}
