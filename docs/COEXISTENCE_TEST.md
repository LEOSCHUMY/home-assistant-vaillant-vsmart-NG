# Original and Next-Gen coexistence observation

Status: initial installation/configuration coexistence verified on one disposable secondary system. This is not a prolonged-runtime, every-control, compatible-upgrade or rollback validation.

## Environment and candidates

- Home Assistant 2026.11.1 / Python 3.14.10, running as a TrueNAS application.
- Official original integration 0.11.2, domain `vaillant_vsmart`, with `vaillant-netatmo-api==0.13.1`.
- NG integration source commit `1d87afe740a00bbfbcf48c8b1a34a5bd761014e1`, domain `vaillant_vsmart_ng`.
- NG library development source commit `eab91cbe180f86bc6b34355e4f30a08e26566fbf`, version `0.3.0.dev0`, import package `vaillant_netatmo_api_ng`.
- The user-built NG wheel SHA-256 was `e6c59e93a6bcc80cf2e601382089e479f9f9588a1302db9b61ec94b74a100ae3`.

The secondary system previously had NG 0.1.0 under the shared domain. The user explicitly treated it as disposable and declined backups. That test state was removed, the old NG library was uninstalled before restoring upstream, and the official original was installed/configured and confirmed functional before NG was added. This clean-baseline reset is not a migration or identity-preservation test.

The staging helper verified 22 NG files against the pinned source commit, added only `custom_components/vaillant_vsmart_ng`, and changed the candidate manifest requirement to the persistent local wheel. It recorded code fingerprints, not account data or backups. After restart and configuration, the user reported both climate entities available and matching device/entity counts.

## Read-only verification reported by the user

| Check | Result |
| --- | --- |
| Original library | 0.13.1 |
| NG library | 0.3.0.dev0 |
| Original and NG client classes | Separate |
| Original integration files | Unchanged |
| Original library files | Unchanged |
| Original entity/device registry counts | 19 entities, 2 devices |
| NG entity/device registry counts | 19 entities, 2 devices |
| Device registry IDs shared between integrations | 0 |

Counts and disjoint registry devices establish distinct registrations in this observation. No claim is made that all unique IDs were compared against a pre-install registry snapshot. No credentials, tokens, raw account payloads or registry identifiers are included in this report.

## Not verified in this test

The user chose to skip prolonged polling and a natural ON/OFF cycle. They remain unverified for this coexistence configuration. Successful initial setup and available climate entities do not establish uninterrupted authentication/updates over time or every command.

The compatible-domain package uses the same implementation, and both variants pass the automated regression suite. The previously published NG 0.1.2/library 0.2.0 installation was field-tested separately. Updating that installation to the new library namespace while preserving its identifiers, and recovering back to the previous version, have not been field-tested. That is a separate scope from the successful new-domain setup above.

The production installation was not changed during this secondary-system experiment. No new stable library or integration release has been published for this candidate.
