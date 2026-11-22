# Secondary field-test candidate

Review-only versions: integration 0.2.1.dev0 and library 0.4.0.dev0. No stable release or PyPI publication is created by these branches or their draft PRs. Do not merge the candidate-only workflow exceptions into a stable release without restoring published dependency pins and the complete published-package audit.

## Exact source

- Integration runtime base: 274235c6e45122c5ff5436af23254d6bd3313859 (merged #29, #30 and #31).
- Library runtime base: e71bdb9f924312877de7da163ca9d52ffae468d7 (merged #15/#16 and corrected docstring).
- Candidate library commit: ee8052845d8e838abe09c2a0d9fa5baaf046a0eb.
- Python source is unchanged from those bases. Candidate changes identify package versions, pin development CI, document scope and prepare installation on the disposable secondary only.
- Both integration domains use the same candidate library; primary and manual-distribution installations are not modified by this preparation.

## Install sequence

1. Read secondary HA/Python/component/library versions and installed file locations without reading credentials or private account storage.
2. Build the pinned library source into a persistent wheel under /config/vsmart-next-field-test/library. Validate its metadata, namespace, Python source and compatible installed dependencies before installation.
3. Stage the pinned new-domain component, overriding only its manifest requirement to that persistent file URL. HA then installs the exact wheel when loading the component, including after a TrueNAS container recreation. Do not use a broad version range or upgrade unrelated HA dependencies.
4. Test updating the existing NG entry first. Compare its device/entity identity and gateway linkage, verify successful polling and absence of via_device deprecation warnings.
5. Then remove/recreate only the NG config entry on the disposable secondary and verify fresh setup beside the original integration. Do not remove the original component or change the primary system.
6. Exercise a manual target, return to schedule, away and return, plus water-heater modes supported by the actual equipment. Compare selected mode/target source logs with HA and the vendor app. The cloud's response latency is not guaranteed.
7. Record results and limitations before selecting and publishing stable versions. Publish the library first, then adopt its stable pin in manifest and both test requirements, restore full audit scope, verify checks and release the integration separately.

The first user command is read-only inventory. This document is not itself an instruction to install or restart HA. Candidate artifacts need a secondary-specific staging/check procedure after that inventory.
