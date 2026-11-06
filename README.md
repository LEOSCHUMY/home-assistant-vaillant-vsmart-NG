# Vaillant vSMART for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/commits/dev)
[![License](https://img.shields.io/github/license/LEOSCHUMY/home-assistant-vaillant-vsmart-NG?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-custom-orange.svg?style=for-the-badge)](https://hacs.xyz)

**Vaillant vSMART** is a Home Assistant custom integration for monitoring and controlling compatible Vaillant vSMART heating systems through the Vaillant cloud service.

This repository is an independently maintained continuation of the upstream project. It is not an official Vaillant or Home Assistant project.

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

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Open the integrations section and select the three-dot menu.
3. Choose **Custom repositories**.
4. Add this repository URL: `https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG`.
5. Select **Integration** as the category and add the repository.
6. Find **Vaillant vSMART** in HACS and install it.
7. Restart Home Assistant.
8. Go to **Settings → Devices & services**, select **Add integration**, and search for **Vaillant vSMART**.

### Manual installation

1. Download or clone this repository.
2. Copy the `custom_components/vaillant_vsmart` directory into the `custom_components` directory of your Home Assistant configuration.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services**, select **Add integration**, and search for **Vaillant vSMART**.

## Configuration

Configuration is performed through the Home Assistant user interface. Follow the integration's setup flow and provide the account and application details requested there.

For background information about obtaining the required client credentials, see the [Home Assistant community discussion](https://community.home-assistant.io/t/added-support-for-vaillant-thermostat-how-to-integrate-in-official-release/31858).

Keep your account credentials and client secrets private. Do not post them in issues, discussions or logs.

## Compatibility and troubleshooting

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
