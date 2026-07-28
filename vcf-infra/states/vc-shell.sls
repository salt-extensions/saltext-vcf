{% import_yaml "templates/vc-shell-template.yaml" as cfg %}

vc-shell:
  vcf_vcenter_shell.shell_access:
    - enabled: {{ cfg.shell.enabled }}
