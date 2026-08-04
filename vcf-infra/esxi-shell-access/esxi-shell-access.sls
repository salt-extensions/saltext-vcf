{% from "esxi-shell-access/map.jinja" import cfg with context %}

{{ cfg.host.name }}:
  module.run:
    - name: vcf_vim_host_security.lockdown_set
    - host: {{ cfg.host.name }}
    - mode: {{ cfg.host.lockdown_mode }}
