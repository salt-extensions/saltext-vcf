{% from "vc-shell/map.jinja" import cfg with context %}

vc-shell:
  vcf_vcenter_shell.shell_access:
    - enabled: {{ cfg.shell.enabled }}
