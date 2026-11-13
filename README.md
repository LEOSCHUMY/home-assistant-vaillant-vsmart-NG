# Vaillant vSMART NG for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/commits/dev)
[![License](https://img.shields.io/github/license/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-custom-orange.svg?style=for-the-badge)](https://hacs.xyz)

**Vaillant vSMART NG** is a Home Assistant custom integration for monitoring and controlling compatible Vaillant vSMART heating systems through the Vaillant cloud service.

> [!IMPORTANT]
> **Unofficial, independent community fork — NOT affiliated with, authorized, sponsored or endorsed by Vaillant or Netatmo.**
> This project is also not an official Home Assistant integration. Neither company provides support for this fork.

This project builds on the [original Vaillant vSMART integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart) and retains its upstream acknowledgements.

## Features

The integration provides the following Home Assistant platforms:

| Platform | Description |
| --- | --- |
| `climate` | Monitor and control the thermostat |
| `number` | Configure the default setpoint duration |
| `select` | View and select the active schedule |
| `sensor` | Thermostat battery and boiler energy/duration measurements |
| `switch` | Control schedules and hot water boost, where supported |
| `water_heater` | Monitor and control domestic hot water |

Available entities and controls depend on the equipment, account and data exposed by the Vaillant cloud service.

From `0.1.1`, room temperatures and heating activity use the same `homestatus` response when valid readings are available, with a fallback to the legacy endpoint. The integration polls approximately every five minutes; it does not provide instant state changes or a guarantee on cloud update latency.

## Installation and migration

> [!WARNING]
> **Already using the original Vaillant vSMART integration?** Do **not** install Vaillant vSMART NG alongside it, remove the existing integration from Home Assistant, or uninstall the original from HACS without following a validated migration procedure. Both use the `vaillant_vsmart` domain and installation directory.
>
> See **[Migration from the original integration](MIGRATION.md)** before changing anything. **Two experimental Marketplace migrations succeeded on Home Assistant 2026.11.1**: the secondary system retained its 2 devices and 19 entities, and the primary TrueNAS system resumed normal operation after transfer, but requires an unsupported internal-storage workaround. It is **not a general or risk-free migration method**, and older standalone HACS remains untested.

### Marketplace / HACS custom repository (new installations only)

1. First check the [GitHub Releases](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases) page for a published release (starting with **v0.1.0**). Until the release exists, the Marketplace may offer a development-branch commit instead; **do not mistake a commit hash for the stable release**.
2. In Home Assistant 2026.11 or newer, open **Settings → Marketplace → Add from link**, and enter `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG`. On older Home Assistant installations with HACS, use **HACS → Custom repositories**, adding it as an **Integration**.
3. Locate **Vaillant vSMART NG** and check the version/source before installing. This fork is not listed in the default catalog.
4. Install the **released version** and restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**, search for **Vaillant vSMART NG**, and complete setup.

**Already configured the original Vaillant vSMART?** Stop here: this new-installation procedure is **not** a migration. Follow [MIGRATION.md](MIGRATION.md) instead.

### Manual installation

1. Download the specific [published release](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases) rather than a moving development branch.
2. Copy the `custom_components/vaillant_vsmart` directory into the `custom_components` directory of your Home Assistant configuration.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services**, select **Add integration**, and search for **Vaillant vSMART NG**.

## Configuration

Configuration is performed through **Settings → Devices & services → Add integration → Vaillant vSMART NG** for a new installation. If you are migrating an existing configured integration, follow [MIGRATION.md](MIGRATION.md) instead of adding another entry.

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

## Compatibility and troubleshooting

The minimum Home Assistant version declared in `hacs.json` is **2024.5** (2024.5.0). It is a minimum installation requirement, not the latest version tested.

For the integration code released as `0.1.1`, with the published `vaillant-netatmo-api-ng==0.1.1` dependency:

| Home Assistant | Verification |
| --- | --- |
| 2024.5.0 | All integration platforms import; 37 regression tests pass in the isolated Python 3.12 compatibility environment |
| 2024.6.4 | Previous baseline: 37 regression tests passed; CI now checks the declared minimum and current HA |
| 2026.11.1 | 37 regression tests pass on Python 3.14; real installation also confirmed heating and idle transitions after polling |

The current CI environment and the frozen minimum-version compatibility environment have different purposes. Historic HA compatibility is not a security recommendation. See [dependency maintenance and security](SECURITY.md) for audit scope and update procedures.

Automated tests mock cloud responses and do not exercise a real boiler. These results do not establish that every intermediate Home Assistant release, every control, or every installation has been tested. Older standalone HACS migration remains unvalidated; see [MIGRATION.md](MIGRATION.md).

`hacs.json` uses the standard integration layout and GitHub release source. No ZIP asset, custom filename, or persistent directory is required. No country restriction is declared: a working compatible Vaillant account and cloud service are required, and the single-installation field test does not establish availability in every country.

- The integration communicates with the Vaillant service over the cloud; an internet connection and a working Vaillant account are required.
- Availability of individual measurements and controls depends on the connected system and the cloud API.
- If setup or communication fails, check the Home Assistant logs and open an [issue](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/issues) with relevant diagnostics. Remove usernames, passwords, tokens and other personal information before sharing logs.

## Maintenance

This repository is maintained by **[LEOSCHUMY](https://github.com/LEOSCHUMY)**.

The maintainer also makes use of **ChatGPT (OpenAI) as an AI assistant** for development support, code review, documentation, troubleshooting and test/CI work. The AI assistant is a support tool, not a project owner or maintainer: project direction, review and publication decisions remain with the human maintainer.

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
