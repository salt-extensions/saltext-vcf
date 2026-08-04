{% from "sddc-personality/map.jinja" import cfg with context %}

{{ cfg.personality.name }}:
  module.run:
    - name: vcf_sddc_personalities.create
    - personality_spec: {{ cfg.personality.spec }}
    - unless:
      - fun: vcf_sddc_personalities.list_
        personality_name: {{ cfg.personality.name }}
