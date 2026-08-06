{% from "usb-controller-removal/map.jinja" import cfg with context %}

usb-controllers-absent:
  vcf_vim_vm_devices.usb_controllers_absent:
    - connected_only: {{ cfg.connected_only }}
