Make ``vcf_vim_vm.present`` parallel-safe (needed when a lab brings up 4 nested VMs concurrently via ``state.orchestrate``) and route standalone-ESXi datastore uploads through the correct endpoint.
