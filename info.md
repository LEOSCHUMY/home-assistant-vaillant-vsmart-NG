# Vaillant vSMART NG (Next-Gen)

**Independent, unofficial community integration — not affiliated with, sponsored or endorsed by Vaillant or Netatmo.**

> This is the unreleased `hacs` work branch. The distinct-domain integration and its isolated library must be published before these installation instructions can be used. Existing published v0.1.2 uses the older shared domain.

## Recommended version

Search for **Vaillant vSMART NG** in HACS or Marketplace and select a published release using domain `vaillant_vsmart_ng`. If it does not appear in your catalog yet, add this repository as a custom integration repository. Select a release, not a development commit. See the [README](README.md) for the installation button and six configuration fields.

The integration provides thermostat controls, schedules, battery and energy/duration sensors, and domestic hot water entities where supported. Room temperature and heating activity prefer valid `homestatus` readings with a legacy fallback; polling is approximately every five minutes.

## Existing shared-domain installation

For continuity of an existing `vaillant_vsmart` configuration, see the [manual compatibility distribution repository](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG-manual). It receives generated output and dedicated instructions from the same source; current snapshots remain unreleased. A new-domain setup does not automatically migrate entity IDs or automations, and manual file replacement does not transfer Marketplace/HACS ownership.

## Verification

On one secondary HA 2026.11.1 system, original 0.11.2 and the new-domain candidate were configured together: both climate entities were available, each had 19 entities and 2 distinct devices, libraries were separate and original files unchanged. Prolonged polling, new ON/OFF transitions, compatible-domain upgrade and rollback were not field-tested. See [the report](docs/COEXISTENCE_TEST.md).

Based on [Mislav Mandarić's original integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart), with license and acknowledgements preserved. Optional support is available on [Ko-fi](https://ko-fi.com/LEOSCHUMY).
