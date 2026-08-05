{% from "vc-statistics/map.jinja" import cfg with context %}

{% for name, spec in cfg.statistics.items() %}
vc-statistics-{{ name }}:
  vcf_vcenter_statistics.interval:
    - name: {{ name }}
    - enabled: {{ spec.enabled }}
    - interval_minutes: {{ spec.interval_minutes }}
    - save_days: {{ spec.save_days }}
    - level: {{ spec.level }}
{% endfor %}
