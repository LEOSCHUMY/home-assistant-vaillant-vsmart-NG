# Vaillant vSMART NG (Next-Gen) — manual compatibility distribution

> [!IMPORTANT]
> **Development review snapshot, not a published installation release.** This export still depends on an unpublished library candidate. Do not install the default branch on a working Home Assistant system. Use only a reviewed, published manual release once one exists.

For new installations, use the **recommended [HACS/Marketplace version](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG)** with domain `vaillant_vsmart_ng`.

This manual distribution retains domain `vaillant_vsmart`. It is intended for existing NG users who want to retain their configuration and entity identity, while receiving the same integration implementation as the recommended version. Preservation is intended, not guaranteed for every version or installation; the current compatible update to the new library has not been field-tested.

This is an independent, unofficial project, not affiliated with, authorized, sponsored or endorsed by Vaillant or Netatmo. It builds on Mislav Mandarić's original integration and preserves the [MIT license](LICENSE) and attribution.

## One maintained implementation

Files in this repository are generated from the main project's canonical integration. Fixes and features belong in the [main source repository](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG), where both variants are tested. Do not edit generated component files here.

Both variants use the same new NG library and API behavior. The installed directory and manifest domain differ. The manual package keeps `custom_components/vaillant_vsmart/`, so it cannot be installed alongside the original integration or another integration using that domain.

This repository is **not a second HACS catalog entry** and does not transfer existing Marketplace/HACS repository ownership. It has no `hacs.json`; installation and updates are manual.

## Before an existing installation is changed

- Confirm the existing domain is `vaillant_vsmart` and record its integration/library versions and entity IDs.
- Keep the existing Home Assistant integration entry; do not delete it or add a replacement entry merely to update files.
- For a working system, retain a restorable HA backup and a copy of the existing component outside `custom_components`.
- Read the release notes and verify the manual release's published library requirement before proceeding. The development candidate currently shown in the default branch is not available on PyPI.

**If Marketplace/HACS currently manages this directory:** file replacement alone does not transfer update ownership. Do not use a delete-and-uninstall action that removes the existing configuration. Do not use the old repository's install/update/uninstall controls to manage the manually replaced copy. A supported management-transfer procedure has not been validated; the historical [migration report](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/hacs/MIGRATION.md) describes an experimental workaround, not a general recommendation. Do not assume this repository makes that transfer automatic.

## Manual update procedure for a published release

These steps describe the intended released package. They are not an instruction to install the current development export.

1. Download a specific **published release** from this manual repository, read its notes, and verify it contains `custom_components/vaillant_vsmart/` with a published library requirement.
2. Stop Home Assistant. Preserve the existing component copy outside the active `custom_components` directory.
3. Replace only the existing `custom_components/vaillant_vsmart/` contents with that release's `custom_components/vaillant_vsmart/` contents. Do not create `vaillant_vsmart_ng` for this compatibility update.
4. Start Home Assistant. It should load the existing entry and install the declared published library; do not run Add integration again when the old entry is present.
5. Compare the existing config entry, devices, entity IDs and representative automations with the recorded baseline. Check a successful update and the applicable controls before treating the update as complete.
6. Repeat this manual process for later releases. There is no automatic HACS update channel for this distribution.

The component files and library requirement must be updated together. Existing NG 0.1.2 or earlier imports the older namespace: upgrading its NG library alone, including indirectly by installing the new-domain variant, would leave that old component unable to import its dependency. Both new variants must agree on the same new NG library version before they are used together.

The new import namespace is `vaillant_netatmo_api_ng`; the old import namespace is not provided as an alias. Do not install development requirements, force library versions or copy packages into HA's Python directory as part of this manual procedure.

## Recovery

If the integration fails to load or identifiers change unexpectedly, stop Home Assistant and restore the previous complete component copy. Ensure its manifest and library requirement belong to that previous release. If configuration or registry data was changed, restore the HA backup. Repository-manager ownership must also be coherent before its controls are used again. A complete compatible-upgrade/rollback exercise for the new namespace remains unvalidated.

## Evidence and limitations

The two variants pass the same coordinator/entity regression tests and packaging checks on minimum/current HA. On the secondary HA 2026.11.1 installation, the **new-domain** candidate was configured beside original 0.11.2: both climate entities were available, each integration retained 19 entities and 2 separate devices, original files were unchanged, and the two library classes were distinct.

That observation is not a test of a compatible-domain upgrade. Prolonged polling, new ON/OFF transitions, the compatible update from library 0.2.0 to the new namespace, and rollback were not field-tested. See the main project's [test report](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/hacs/docs/COEXISTENCE_TEST.md).

## Generated provenance

- Source base commit: [@@SOURCE_COMMIT@@](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/commit/@@SOURCE_COMMIT@@).
- Source working tree modified at export: **@@SOURCE_DIRTY@@**.
- Manifest version: `@@VERSION@@` (this does not mean a release has been published).
- `distribution.json` records the source identity, requirements and generated file hashes.

The verification workflow checks these hashes and manifest consistency; runtime regression tests run in the main source repository. A dirty export is a local preview, not evidence of an exact committed source snapshot.

## Support development

If the project is useful, you can optionally support maintenance of the NG fork on [Ko-fi](https://ko-fi.com/LEOSCHUMY). Contributions, testing and bug reports are equally welcome.
