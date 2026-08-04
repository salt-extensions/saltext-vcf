{% from "esxi-kernel-module/map.jinja" import cfg with context %}

esxi-kernel-module:
  vcf_vim_host_kernel_module.options_set:
    - host: {{ cfg.host }}
    - module: {{ cfg.module }}
    - options: {{ cfg.options }}
