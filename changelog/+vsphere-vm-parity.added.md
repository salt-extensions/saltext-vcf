Added ``vmware_vm`` parity surface: ``vcf_vim_vm.list_templates``,
``vcf_vim_vm.path``, ``vcf_vim_vm.info``, ``vcf_vim_vm.register_all``,
``vcf_vim_vm.unregister_all`` (with graceful ``shutdown=``),
``vcf_vim_vm_console.get_ticket``, ``vcf_vcenter_vm.deploy_ovf`` /
``deploy_ova`` exec entrypoints (raw-OVF sources supported), and the
``vcf_vim_vm_boot`` client/module/state (boot order, delay, BIOS setup,
boot retry, EFI secure boot) with ``vcf_vim_vm_boot.boot_manager``.
