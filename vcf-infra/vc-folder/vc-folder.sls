{% from "vc-folder/map.jinja" import cfg with context %}

{{ cfg.folder.name }}:
  vcf_vcenter_folder.present:
    - folder_type: {{ cfg.folder.type }}
    {%- if cfg.folder.parent %}
    - parent: {{ cfg.folder.parent }}
    {%- else %}
    - datacenter: {{ cfg.folder.datacenter }}
    {%- endif %}
