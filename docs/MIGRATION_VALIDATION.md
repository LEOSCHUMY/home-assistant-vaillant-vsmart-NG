# Migration validation plan

Status: **proposal**, not an installation procedure or a supported migration tool.

## Goal and boundaries

Transfer an original Vaillant vSMART installation to NG while preserving its Home Assistant config entry, device/entity identifiers and automation references, and leave update management pointing to NG.

Treat these as separate concerns: Home Assistant configuration/registries, installed integration files and library requirement, and Marketplace/HACS repository ownership. Sharing a domain helps preserve identity but does not itself transfer update ownership.

Current observations and the experimental workaround are in [MIGRATION.md](../MIGRATION.md). The successful NG-to-NG update on 2026-11-17 started from NG 0.1.1 with a temporary library 0.2.0 field-test requirement. Do not label it a clean stock upgrade, a rollback test or proof of original-to-NG transfer support.

## Supported-path investigation

Reviewed on 2026-11-17:

- [Marketplace domain ownership documentation](https://contributors.home-assistant.io/marketplace/guides/integrations/#pick-a-domain-that-is-yours).
- HA 2026.11.1 [integration repository implementation](https://github.com/home-assistant/core/blob/2026.11.1/homeassistant/components/marketplace/repositories/integration.py).
- HA 2026.11.1 [repository commands](https://github.com/home-assistant/core/blob/2026.11.1/homeassistant/components/marketplace/websocket/repository.py) and [repository-list commands](https://github.com/home-assistant/core/blob/2026.11.1/homeassistant/components/marketplace/websocket/repositories.py).
- [Legacy HACS 2.0.5 integration repository implementation](https://github.com/hacs/integration/blob/2.0.5/custom_components/hacs/repositories/integration.py), as a historical reference only.

The reviewed Marketplace installer refuses a domain owned by another installed repository. Its uninstall endpoint refuses removal while config entries for that domain exist. No fork-ownership transfer command was found in the reviewed commands. This does not establish behavior in other versions or make direct storage editing supported. The legacy HACS file review is insufficient to endorse a standalone-HACS migration sequence.

Before implementing a transfer, establish whether an applicable supported UI/API exists or whether a Marketplace enhancement is required. Do not treat GitHub repository rename/transfer, HACS-to-Marketplace takeover or catalog inclusion as fork-transfer support. Do not post to external maintainers without the project maintainer's authorization.

## Proposed read-only preflight

No script has been implemented yet. Agree on the supported input formats and available APIs before choosing how to collect data.

The first tool should only inspect and compare:

- Home Assistant version, original/NG manifest identity and published requirement.
- Selected target release identity and manifest, rather than a moving development branch.
- Installation manager and repository ownership where an applicable read-only interface exposes them. Report unknown when it cannot be determined.
- Counts and locally retained identifiers for this integration's config entries, devices and entities; flag duplicate domains or ambiguous identity.
- A baseline and a post-change snapshot, with a comparison of retained/missing/added identifiers.

Do not fetch tokens, include config-entry credential data, print complete storage objects, call boiler controls, install packages or modify files in the user's configuration. Keep raw identity snapshots local; shared output should summarize differences without names or device identifiers. Tool output must not claim that the existence of a backup proves it can be restored.

Use synthetic fixtures for development. A future implementation needs meaningful tests for missing data, duplicate/conflicting records, unsupported storage/API versions and redaction before it is offered for use.

## Isolated validation matrix

Use a disposable secondary Home Assistant instance with a verified restore path. Record exact HA, manager and integration versions in every test.

| Case | What to establish | Current evidence |
| --- | --- | --- |
| Manual original → tagged NG | Replace files while retaining the existing config entry; validate identity and dependency installation | Procedure documented; final-release end-to-end validation pending |
| Marketplace original → tagged NG | Supported ownership transfer, preserved configuration and working NG update tracking | Two experimental transfers to NG 0.1.0 used private-storage edits |
| Standalone HACS original → tagged NG | Version-specific manager behavior and preserved configuration | Not validated |
| Stock NG 0.1.1 → NG 0.1.2 | Normal update using published dependencies and preserved identifiers | Not separately validated; production observation had a temporary field-test manifest |
| NG after field test → NG 0.1.2 | Published manifest replaces the local-wheel requirement | Observed on HA 2026.11.1; versions/icons and an OFF poll verified |
| NG → original recovery | Restore files, configuration and manager ownership coherently | Not validated |

A valid before/after check includes config-entry identity, entity IDs and unique IDs, device associations, representative automation references, a successful poll and applicable controls. Use only a simulator or explicitly authorized test equipment for commands. Separately verify update tracking after restart.

## Completion criteria

- A supported path is identified, or the lack of one is clearly documented.
- Each recommended path is tested with its exact release and manager versions.
- Identifier preservation and manager ownership are both checked.
- Recovery is tested before a broad recommendation.
- Evidence distinguishes synthetic tests, source inspection and actual installation observations.
- Production configuration is not used to discover new transfer or rollback procedures.

Until then, keep the original-to-NG workaround labeled experimental. This plan does not authorize automatic private-storage edits or claim the existing workaround is generally safe.
