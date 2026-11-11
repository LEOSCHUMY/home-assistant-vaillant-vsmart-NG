# Migrating to Vaillant vSMART NG

> [!IMPORTANT]
> **Vaillant vSMART NG replaces the original integration; it is not a second integration to install alongside it.**
> Both use the Home Assistant domain `vaillant_vsmart` and the same installation directory, `/config/custom_components/vaillant_vsmart`. Do **not** add a second integration entry in **Settings → Devices & services**.
>
> This is an independent community fork, not affiliated with or endorsed by Vaillant or Netatmo.

## Migration status

**Before installing, verify that the [v0.1.0 GitHub Release](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases/tag/v0.1.0) exists.** Until it is published, Marketplace may show the current development commit instead. This guide does not treat such a commit as a published release.

- **Existing manually installed integrations:** a controlled file replacement is described below, but should be tested with the final release archive before being recommended as generally proven.
- **Existing Marketplace-managed installations of the original integration:** one **experimental** migration succeeded on Home Assistant **2026.11.1**, retaining its configuration and entity IDs. The steps below involve editing an internal Marketplace storage file, are not officially supported, and have not been validated across installations. Standard direct installation of NG over the original was blocked by directory ownership. **Do not use Delete and uninstall on the original** if you need to preserve the configuration.
- **Existing standalone/older HACS installations:** an in-place transfer has **not been tested** and is not covered by the Marketplace workaround.
- **Fresh installations:** once NG has a GitHub Release, it can be added as a custom repository using **Settings → Marketplace → Add from link** on Home Assistant 2026.11+, or as a [HACS custom repository](https://hacs.dev/docs/faq/custom_repositories/) on older versions. It is **not** listed in the default catalog.

## Before touching an existing installation

1. Make a **full Home Assistant backup** and verify that you can restore it. Store a copy **outside** the Home Assistant host (for example, on your PC).
2. Save a separate copy of the entire existing `/config/custom_components/vaillant_vsmart/` directory, including its `manifest.json`. Record the original integration version and installation method (HACS or manual).
3. Record the existing `entity_id` values used by dashboards, scripts and automations. For critical automations, check that you can restore their configuration.
4. Confirm that your Home Assistant installation and backup are working **before** changing files. Plan a short maintenance window.
5. **Do not delete the existing integration in Settings → Devices & services.** Removing a Home Assistant config entry can also remove entity/device registry entries; keeping the same technical domain is important for preserving the installation.

## Existing installation made manually — controlled replacement (to validate)

Use this route only if the original integration was **not being managed by HACS**, and only once the `v0.1.0` release is available.

1. Download the **specific NG release tag `v0.1.0`** from [the NG repository](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases). Do not use a changing development branch as the source.
2. Stop Home Assistant cleanly. Preserve the entire backup copy of `custom_components/vaillant_vsmart/` outside the active `custom_components` directory.
3. Replace the contents of **the existing** `/config/custom_components/vaillant_vsmart/` directory with the files from that release's `custom_components/vaillant_vsmart/` directory. **Do not create a second directory** such as `vaillant_vsmart_ng`.
4. Check that the installed `manifest.json` identifies `Vaillant vSMART NG`, has `"domain": "vaillant_vsmart"`, version `0.1.0`, and requires `vaillant-netatmo-api-ng==0.1.0`.
5. Start Home Assistant and verify that the pre-existing integration entry loads. **Do not run Add integration again** if the existing entry is already configured.
6. Compare the device list and recorded `entity_id` values against the backup. Check heating controls, schedules, hot-water entities and automations as applicable. Confirm that room temperature updates using `homestatus` and that the Home Assistant logs show no dependency-installation or setup errors.

**Important:** Preserving the domain and identifiers is intended to preserve existing configuration and entities, but this must be verified on the target installation; it is not a guarantee for every upstream version or custom configuration.

## Existing original installation managed by Home Assistant 2026.11 Marketplace — experimental migration

> [!CAUTION]
> **Unofficial workaround; not a supported one-click migration.** Editing `.storage/marketplace.repositories` directly can leave Marketplace metadata inconsistent or be overwritten by Home Assistant. Only proceed with a tested **full backup**, an additional copy of this storage file, and a disposable/secondary installation first. Do not use **Delete and uninstall** on the original integration: that action also removes its Home Assistant configuration. This has been observed on **one** Home Assistant 2026.11.1 instance; it is **not validated** on other versions, other setups, or older HACS installations.

### Observed test (Home Assistant 2026.11.1)

On a secondary Home Assistant installation, the original Marketplace-managed **Vaillant vSMART v0.11.2** (repository `MislavMandaric/home-assistant-vaillant-vsmart`) had **2 devices and 19 entities**, with existing entity IDs recorded before the test.

- NG `v0.1.0` was added as a custom repository using Marketplace → **Add from link**. Adding it did not change the installed original.
- Trying to install NG failed with: `The vaillant_vsmart directory belongs to MislavMandaric/home-assistant-vaillant-vsmart.`
- The original's **Uninstall** option displayed a warning requiring **Delete and uninstall**, including removal of the configured integration. **That action was not used.**
- In the original repository's entry in `/config/.storage/marketplace.repositories`, `"installed": true` was present; NG's entry had no such field.
- After disabling Marketplace, restarting Home Assistant, and removing **only** the original repository entry's `"installed": true,` property in an offline editing step, Marketplace was re-enabled. It then showed the original as **Not installed** while Home Assistant still retained the existing Vaillant configuration.
- Installing the officially tagged NG `v0.1.0` release through Marketplace then completed without an ownership-conflict error.
- After the requested Home Assistant restart, the user confirmed NG `v0.1.0` installed, original marked not installed, and the pre-existing **2 devices, 19 entities and entity IDs preserved**.

This demonstrates a successful migration **for that one test environment**. It does **not** establish that the workaround is generally safe, that all older HACS versions behave the same, or that future Marketplace updates and rollback work correctly. Do not treat the previous registry-edit action as an officially endorsed migration.

### Experimental sequence reproduced

1. Record the Home Assistant version, original integration version, and the existing entity IDs/device count. Back up Home Assistant completely and retain an off-host copy of `/config/custom_components/vaillant_vsmart/`.
2. Copy `/config/.storage/marketplace.repositories` to a separate off-host backup. Keep the original integration configured in **Settings → Devices & services**.
3. Register `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG` as a custom repository in Marketplace; confirm it offers a tagged NG release (not a moving commit hash).
4. **Do not uninstall the original**. In its Marketplace uninstall confirmation, **Delete and uninstall** would delete the configured integration.
5. Find the Marketplace integration's own **Disable** control, disable it, and restart Home Assistant with Marketplace disabled. Check that the existing Vaillant integration still exists. If you cannot reliably stop Marketplace or maintain backups, **stop here**.
6. With Marketplace inactive, open `/config/.storage/marketplace.repositories`, locate **only** the record whose `full_name` exactly equals `MislavMandaric/home-assistant-vaillant-vsmart`, and remove **only** its `"installed": true,` line/property. Keep the other keys (including `installed_commit`, `version_installed`) and NG's record unchanged. Preserve valid JSON. **Do not edit** `core.config_entries`, `core.entity_registry` or device registries.
7. Re-enable Marketplace (if hidden in the integrations list, open **Settings → Marketplace → Open integration page**) and confirm it now lists the original as **Not installed**, while the existing configured Vaillant integration still exists.
8. Install **Vaillant vSMART NG `v0.1.0`** through Marketplace. If the old directory-ownership error remains, or any other error appears, **stop** rather than forcing further changes.
9. Check that Marketplace lists NG as **Installed**, `v0.1.0`, and the original as **Not installed**. Restart Home Assistant when requested. Do **not** create another integration config entry.
10. Confirm that the pre-existing devices and entity IDs remain (the test retained **2 devices and 19 entities**), temperature readings refresh on the existing polling schedule, controls behave as expected, and no new dependency/setup errors occur. Also verify future update tracking points to NG before trusting Marketplace upgrades.

**For other users:** this is a reproducible **experimental** report, not a guarantee. Restore the full backup if configuration or registry state becomes inconsistent. Home Assistant Marketplace may change its storage format and behavior in future versions.

## Original installation managed by older HACS — not validated

The workaround above was tested only with the **integrated Home Assistant Marketplace on 2026.11.1**. Do not apply it to standalone/older HACS storage files without a separate validation. Never install original and NG simultaneously, delete the Home Assistant configuration to clear the conflict, or assume manual file replacement also transfers Marketplace/HACS update ownership.

## New installation with Marketplace/HACS (after the first NG release)

1. Confirm that the NG `v0.1.0` GitHub Release exists; do not accidentally install a commit-hash development snapshot.
2. On Home Assistant 2026.11+, open **Settings → Marketplace → Add from link**. On older HACS-based installations, use **HACS → Custom repositories**, category **Integration**.
3. Add `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG`.
4. Find **Vaillant vSMART NG** and install the released version; restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and search for **Vaillant vSMART NG**; complete setup.

These steps are intended for users who **do not have an existing `vaillant_vsmart` installation or config entry**.

## Recovering from a failed migration

1. If Home Assistant does not load the integration, or existing entities disappear, **do not delete the config entry, reset devices or create duplicate entries**.
2. Preserve a copy of the logs with sensitive information removed; do not share usernames, passwords, tokens, serial numbers or complete API payloads.
3. Stop Home Assistant, restore the previously saved `custom_components/vaillant_vsmart/` directory and its original `manifest.json`, then restart. If Marketplace/HACS managed the previous version, verify that repository tracking and installed files match before using its update controls.
4. If the configuration or entity registry was changed or the rollback fails, restore the **full Home Assistant backup**.

## Known compatibility note

Home Assistant 2026.11 may warn about firmware `sw_version` being passed as an integer by the upstream-derived integration. Compatibility with Home Assistant 2026.12 requires a separate fix; this warning is unrelated to PyPI installation or the `homestatus` temperature data path.

## Feedback

For NG-specific bugs or migration reports, use the [NG issue tracker](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/issues) and include Home Assistant version, HACS version (if used), source installation method and sanitized logs.
