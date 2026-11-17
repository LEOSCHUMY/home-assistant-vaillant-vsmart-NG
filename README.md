# Vaillant vSMART NG (Next-Gen) for Home Assistant

<img src="custom_components/vaillant_vsmart_ng/brand/icon.png" width="96" alt="Vaillant vSMART NG">

> [!IMPORTANT]
> **Unreleased work on branch `hacs`.** The new-domain version below is not published yet, and its library candidate is not available on PyPI. Published integration `v0.1.2` still uses the older `vaillant_vsmart` domain. Do not install that release or this development branch as if it were the new-domain catalog release. See [build status and release gates](docs/BUILD_VARIANTS.md).

[![GitHub Release](https://img.shields.io/github/v/release/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases)
[![License](https://img.shields.io/github/license/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](LICENSE)
[![Support development on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20development-FF5E5B?logo=ko-fi&logoColor=white&style=for-the-badge)](https://ko-fi.com/LEOSCHUMY)

**Vaillant vSMART NG — Next-Gen** is a community-maintained Home Assistant integration for compatible Vaillant vSMART heating systems. It reads room temperatures and heating activity from the Vaillant cloud's `homestatus` endpoint when valid, with a legacy fallback.

> **Unofficial and independent:** not affiliated with, authorized, sponsored or endorsed by Vaillant or Netatmo, and not an official Home Assistant integration. This project builds on [Mislav Mandarić's original integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart), with its license and acknowledgements preserved.

## Recommended: HACS / Marketplace

The recommended version uses the distinct domain **`vaillant_vsmart_ng`**. Search for **Vaillant vSMART NG** in HACS or Marketplace and choose its published new-domain release.

[![Open Vaillant vSMART NG in HACS or Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LEOSCHUMY&repository=home-assistant-vaillant-vsmart-NG&category=integration)

1. Open HACS or, on Home Assistant 2026.11+, **Settings → Marketplace**, and search for **Vaillant vSMART NG**.
2. Select a published release whose manifest domain is `vaillant_vsmart_ng`. The currently published `v0.1.2` predates this domain change; wait for the new-domain release before following this path.
3. Install it and restart Home Assistant when requested.
4. Open **Settings → Devices & services → Add integration**, select **Vaillant vSMART NG**, and complete setup.

If the repository is not yet shown in your catalog, the button can add it as a custom integration repository. You can also add `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG` through **Marketplace → Add from link**, or HACS **Custom repositories → Integration**, then select the published new-domain release. A development commit is not a stable release.

## Already using the original or an older NG installation?

The new-domain version is a separate Home Assistant integration. Initial coexistence with original `0.11.2` was verified on a secondary HA 2026.11.1 system, but it does not automatically move existing entries, device/entity IDs or automation references. The [test report](docs/COEXISTENCE_TEST.md) records the exact scope and unverified parts.

**Older NG releases need special care:** NG 0.1.2 and earlier import the older NG library namespace. Installing the new library alongside that unchanged component would break those imports because both versions use the same NG distribution name. Update the existing component and its requirement together through the compatible route before considering a new-domain NG installation beside it. The successful coexistence test used the official original integration, not an unchanged older NG component.

If you want to retain an existing `vaillant_vsmart` entry, read the **[manual compatibility distribution guide](distribution/manual/README.md)** instead. The dedicated manual distribution repository is being prepared; this link currently opens its source instructions. It receives generated output from this same implementation and uses the same NG library. It is intended for manual updates and is not a second catalog entry.

The compatible update to the new library namespace and its rollback have not been field-tested. Repository-manager ownership is a separate issue from replacing files; do not assume manual replacement transfers HACS/Marketplace tracking. Historical shared-domain experiments are documented in [MIGRATION.md](MIGRATION.md), not presented as a general migration procedure.

## Features

| Platform | Description |
| --- | --- |
| `climate` | Thermostat temperature, heating activity and controls |
| `number` | Default setpoint duration |
| `select` | Active schedule selection |
| `sensor` | Battery and boiler energy/duration measurements |
| `switch` | Schedules and hot water boost, where supported |
| `water_heater` | Domestic hot water monitoring and control |

Polling remains approximately every five minutes; this is not instant status or a cloud-latency guarantee. Available entities and controls depend on the equipment, account and API responses.

## Configuration

Configure the new-domain version through **Settings → Devices & services → Add integration → Vaillant vSMART NG**. An existing original/shared-domain entry remains separate; adding this integration does not migrate its entity IDs or automations. For an update of the compatible manual variant, retain the existing entry and follow the [manual distribution instructions](distribution/manual/README.md).

The setup form still requires all six fields below. The integration uses them to request an access token; none of these fields is obsolete.

| Setup field | Vaillant vSMART example | MiGo example |
| --- | --- | --- |
| Client ID | `na_client_android_vaillant` | `na_client_android_sdbg` |
| Client secret | The application client secret matching the vSMART Client ID | The application client secret matching the MiGo Client ID |
| Username | Your vSMART app account username | Your MiGo app account username |
| Password | Your vSMART app account password | Your MiGo app account password |
| User prefix | `vaillant` | `sdbg` |
| App version | `1.0.4.0` | `1.3.0.4` |

These public application identifiers and version strings are the examples documented by the [original integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart#configuration-is-done-in-the-ui). They are provided as setup guidance, not as a claim that a fresh login with each combination was tested for this NG release. MiGo has not been field-tested with NG.

**Client secret is not your account password.** It belongs to the application identified by Client ID, while Username and Password belong to your app account. For background on obtaining the matching application credentials, see the [Home Assistant community discussion](https://community.home-assistant.io/t/added-support-for-vaillant-thermostat-how-to-integrate-in-official-release/31858).

**App version is sent to the cloud authentication API.** It is not the Home Assistant version or the NG integration version. Keep the Client ID, Client secret, User prefix and App version appropriate to the same application.

Keep your account credentials and client secrets private. Do not post them in issues, discussions or logs.

## Compatibility and verification

The Home Assistant minimum remains **2024.5**, as declared in `hacs.json`. Both generated integration variants use the same isolated `vaillant_netatmo_api_ng` library. The `hacs` work branch currently tests unpublished candidate `0.3.0.dev0` from an exact source commit; a published library requirement will replace that development setup before release.

| Environment | Evidence |
| --- | --- |
| HA 2024.5.0 / Python 3.12 | Same 37 regressions per generated variant, plus packaging/staging checks and platform imports |
| HA 2026.11.1 / Python 3.14 | Same automated matrix for both variants |
| Secondary HA 2026.11.1 / Python 3.14.10 | Original 0.11.2 and new-domain NG candidate configured together; both climate entities available, 19 entities and 2 distinct devices each, separate libraries and original files unchanged |

The user chose not to run prolonged polling or a new ON/OFF cycle for that coexistence test. The compatible-domain upgrade from published NG 0.1.2/library 0.2.0 to the new namespace, and rollback, remain unverified on the field. Earlier shared-domain temperature/heating observations are historical evidence, not a test of the new configuration. See [the full report](docs/COEXISTENCE_TEST.md).

Automated tests mock cloud data. They do not establish real authentication on every device, every control or compatibility with every intermediate HA version. Historic HA compatibility is not a security recommendation; [SECURITY.md](SECURITY.md) explains audit scope.

A working compatible Vaillant account and internet connection are required. If setup or updates fail, check HA logs and open an issue with sanitized diagnostics; never share credentials, tokens, serial numbers or complete account payloads.

## Maintenance

This repository is maintained by **[LEOSCHUMY](https://github.com/LEOSCHUMY)**.

The maintainer also makes use of **ChatGPT (OpenAI) as an AI assistant** for development support, code review, documentation, troubleshooting and test/CI work. The AI assistant is a support tool, not a project owner or maintainer: project direction, review and publication decisions remain with the human maintainer.

## Support development

If this project is useful to you, you can optionally support maintenance of the NG fork with a tip on [Ko-fi](https://ko-fi.com/LEOSCHUMY).

Contributions, testing and bug reports are equally welcome.

## Contributing

Bug reports, suggestions and pull requests are welcome. Please read the [contribution guidelines](CONTRIBUTING.md) before submitting changes.

When reporting a problem, include the Home Assistant version, integration version and relevant sanitized logs. Never include credentials, tokens or other secrets.

## Credits and acknowledgements

This project builds on the work of the original [Vaillant vSMART integration by MislavMandaric](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart), whose work made this continuation possible.

The original project also acknowledged:

- [oncleben31's Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component)
- [Ludeeus's integration blueprint](https://github.com/custom-components/integration_blueprint)
- [pjmaenh's original Vaillant integration](https://github.com/pjmaenh/home-assistant-vaillant)
- [philippelt](https://github.com/philippelt), [jabesq](https://github.com/jabesq), [samueldumont](https://github.com/samueldumont) and [superbunika](https://github.com/superbunika) for their contributions and API research.

Thanks to the original authors and all community members who have contributed knowledge, testing and feedback.
