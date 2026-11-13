# Dependency maintenance and security

## Runtime versus development

Home Assistant installs the integration requirement from custom_components/vaillant_vsmart/manifest.json. requirements.txt describes a separate development/regression environment and does not upgrade or downgrade the user's Home Assistant. Keep the published library requirement aligned with the manifest; CI checks this. A library change must be released before the integration can adopt a new version.

The current regression environment uses HA 2026.11.1 / Python 3.14 and the published library 0.1.1. The maintained tests use a small real-HA fixture with a mocked cloud client. They test coordinator/entity behavior, not integration config-entry loading, real authentication or every device control. No third-party HA test harness or resolver overrides are needed.

requirements-compat.txt is an isolated HA 2024.5.0 / Python 3.12 compatibility environment. Its historic core dependencies can have known vulnerabilities: passing those tests establishes API compatibility only. Do not deploy it as a security baseline or use its package versions to downgrade a running HA installation. Dependabot deliberately excludes this fixed compatibility file. The minimum in hacs.json is unchanged and does not certify that old HA releases are secure.

## Audits and updates

The Dependency security workflow installs the current requirements into a clean environment and runs pip-audit from a separate tools environment, scanning the current environment's site-packages. It does not scan the frozen historic compatibility environment. There are no ignored vulnerability IDs or continue-on-error. It runs on PRs, pushes, a weekly schedule and manual dispatch; database/network errors also fail it. A successful audit means no known advisories were returned for those resolved versions at that time, not that the software is free of all vulnerabilities or that users have the same versions installed.

Dependabot groups Python and GitHub Actions version updates weekly. It does not merge or publish. Review HA/library compatibility and run the tests before accepting an update. Do not add global dependency overrides to the integration to bypass HA's package constraints.

On a GitHub fork, explicitly enable Dependabot version updates in Settings > Advanced Security (wording may vary), plus the dependency graph, alerts and security updates. A committed dependabot.yml alone is not proof that these settings are enabled.

For a production installation, collect package version metadata read-only and audit it in a separate environment. Never install development requirements or an audit scanner into the production HA container.
