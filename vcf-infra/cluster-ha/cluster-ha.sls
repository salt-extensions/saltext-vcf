{% from "cluster-ha/map.jinja" import cfg with context %}

vcf_cluster_ha:
  vcf_vim_cluster_config.ha:
    - cluster: {{ cfg.cluster.name }}
    - enabled: {{ cfg.ha.enabled }}
    - host_monitoring: {{ cfg.ha.host_monitoring }}
    - vm_monitoring: {{ cfg.ha.vm_monitoring }}
    - restart_priority: {{ cfg.ha.restart_priority }}
    - isolation_response: {{ cfg.ha.isolation_response }}
    - admission_control_enabled: {{ cfg.ha.admission_control_enabled }}
