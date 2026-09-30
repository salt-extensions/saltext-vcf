Fixed the ``check-cli-examples`` and ``make-autodocs`` pre-commit hooks,
which still pointed at the pre-rename ``src/saltext/vmware`` paths and
were silently doing nothing; they now run against ``src/saltext/vcf``
(the two pre-existing ``vcf_vcenter_vm`` functions without CLI examples
were fixed in the process).
