# Vaillant vSMART NG

> **Independent, unofficial community integration — not affiliated with, sponsored or endorsed by Vaillant or Netatmo.**

[![GitHub Release](https://img.shields.io/github/v/release/LEOSCHUMY/home-assistant-vaillant-vsmart-NG)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases)
[![License](https://img.shields.io/github/license/LEOSCHUMY/home-assistant-vaillant-vsmart-NG)](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/dev/LICENSE)

NG starts its own release series at `0.1.0`; its version numbers do not track upstream releases. The integration retains the `vaillant_vsmart` domain and directory.

## Features

| Platform | Description |
| --- | --- |
| `climate` | Thermostat temperature, heating activity and controls |
| `number` | Default setpoint duration |
| `select` | Active schedule selection |
| `sensor` | Battery and boiler energy/duration measurements |
| `switch` | Schedules and hot water boost, where supported |
| `water_heater` | Domestic hot water monitoring and control |

From `0.1.1`, room temperatures and heating activity use valid `homestatus` readings with a legacy fallback. Polling remains approximately every five minutes; cloud update latency is not guaranteed. Availability depends on the equipment and API responses.

## Existing original Vaillant installation

**Read [MIGRATION.md](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/dev/MIGRATION.md) before installing NG.** Original and NG use the same domain and directory. Do not install them alongside each other, delete the existing Home Assistant config entry, or assume uninstalling the original preserves it.

The reported Marketplace migrations used NG `0.1.0` and an experimental internal-storage workaround on Home Assistant 2026.11.1. They are not a supported general migration procedure; older standalone HACS and future Marketplace updates require separate validation.

## New installation

1. Select a specific [published NG release](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/releases), not a moving development commit.
2. Add this repository as a custom integration repository in Marketplace/HACS. It is not currently in the default catalog.
3. Install the released version and restart Home Assistant.
4. Add **Vaillant vSMART NG** through **Settings → Devices & services** and complete the UI setup.

See [README.md](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/dev/README.md) for installation and compatibility details. Keep account credentials and client secrets private.

## Credits

Based on [Mislav Mandarić's original Vaillant vSMART integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart), with the original MIT attribution and community acknowledgements retained in the [README](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/dev/README.md) and [LICENSE](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/blob/dev/LICENSE).
