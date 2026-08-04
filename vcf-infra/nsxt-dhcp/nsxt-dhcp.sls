{% from "nsxt-dhcp/map.jinja" import cfg with context %}

{{ cfg.server.id }}:
  module.run:
    - name: vcf_nsx_dhcp.server_create
    - server_id: {{ cfg.server.id }}
    - server_address: {{ cfg.server.spec.server_address }}
    - lease_time: {{ cfg.server.spec.lease_time }}

{{ cfg.relay.id }}:
  module.run:
    - name: vcf_nsx_dhcp.relay_create
    - relay_id: {{ cfg.relay.id }}
    - server_addresses: {{ cfg.relay.server_addresses }}
