# Migrating to Vaillant vSMART NG

> [!IMPORTANT]
> **Vaillant vSMART NG replaces the original integration; it is not a second integration to install alongside it.**
> Both use the Home Assistant domain `vaillant_vsmart` and the same installation directory, `/config/custom_components/vaillant_vsmart`. Do **not** add a second integration entry in **Settings → Devices & services**.
>
> This is an independent community fork, not affiliated with or endorsed by Vaillant or Netatmo.

## Migration status

**The first NG integration release `v0.1.0` has not yet been published.** These instructions are being prepared **before** that release.

- **Existing manually installed integrations:** a controlled file replacement is described below, but should be tested with the final release archive before being recommended as generally proven.
- **Existing HACS-managed installations of the original integration:** the HACS-to-HACS ownership transfer is **not yet validated**. **Do not follow an untested sequence of HACS Remove / Uninstall and NG Install.** HACS manages files in the same directory for both repositories, and removing a repository can remove its installed files. We will document an exact, tested switching procedure here before recommending an in-place migration.
- **Fresh installations:** once NG has a GitHub Release, it can be added as a [HACS custom repository](https://hacs.dev/docs/faq/custom_repositories/). It is **not** currently listed in HACS's default catalog.

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

## Existing original integration managed by HACS — migration pending validation

Do **not** install both original and NG simultaneously. Adding NG as a custom repository while the original is still installed **does not mean the migration is complete**.

Until an end-to-end HACS-to-HACS migration is tested and documented:

- Do **not** remove the original integration from **Settings → Devices & services**.
- Do **not** use HACS **Remove/Uninstall** as a first step without a verified backup and a tested procedure. HACS can delete the shared installation directory.
- Do **not** overwrite the HACS-managed original integration manually and assume that future HACS updates will keep managing the NG fork: HACS may still track the original repository.
- Keep the existing installation as-is, or seek individualized migration instructions with the installed HACS version, Home Assistant version, and original repository identification. Never share credentials or tokens.

**Release gate:** Before advertising a seamless HACS migration, test it on a nonproduction Home Assistant instance, record the exact UI sequence and verify that both HACS's update source and Home Assistant's existing config entry are correct after restart. This section will then be updated.

## New installation with HACS (after the first NG release)

1. Open HACS → menu → **Custom repositories**.
2. Add `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG` with category **Integration**.
3. Find **Vaillant vSMART NG** and download the released version.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and search for **Vaillant vSMART NG**; complete setup.

These steps are intended for users who **do not have an existing `vaillant_vsmart` installation or config entry**.

## Recovering from a failed migration

1. If Home Assistant does not load the integration, or existing entities disappear, **do not delete the config entry, reset devices or create duplicate entries**.
2. Preserve a copy of the logs with sensitive information removed; do not share usernames, passwords, tokens, serial numbers or complete API payloads.
3. Stop Home Assistant, restore the previously saved `custom_components/vaillant_vsmart/` directory and its original `manifest.json`, then restart. If HACS managed the previous version, verify that HACS tracking and installed files match before using its update controls.
4. If the configuration or entity registry was changed or the rollback fails, restore the **full Home Assistant backup**.

## Known compatibility note

Home Assistant 2026.11 may warn about firmware `sw_version` being passed as an integer by the upstream-derived integration. Compatibility with Home Assistant 2026.12 requires a separate fix; this warning is unrelated to PyPI installation or the `homestatus` temperature data path.

## Feedback

For NG-specific bugs or migration reports, use the [NG issue tracker](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/issues) and include Home Assistant version, HACS version (if used), source installation method and sanitized logs.
