{% import_yaml "templates/role-template.yaml" as cfg %}

{{ cfg.role.name }}:
  vcf_vim_role.present:
    - privileges: {{ cfg.role.privileges }}