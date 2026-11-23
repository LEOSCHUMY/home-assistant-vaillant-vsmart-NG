# Maintained regression tests

Use Python 3.14 for the current Home Assistant environment:

Both regression environments install published library `0.4.0` from PyPI. Do not use these development requirements in a running HA installation.

```bash
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --no-deps vaillant-netatmo-api==0.13.1
python -m pip check
python -m pytest -q tests/test_build_variants.py tests/test_secondary_installer.py tests/test_manual_export.py
python scripts/build_variants.py --output artifacts/variants
python scripts/test_variant.py --variant hacs --artifacts artifacts/variants
python scripts/test_variant.py --variant legacy --artifacts artifacts/variants
```

For the isolated HA 2024.5.0 compatibility job, create a separate Python 3.12 environment and install requirements-compat.txt instead. Do not mix the two environments. Historic dependencies are not a production security baseline; see ../SECURITY.md.

conftest.py creates a real HomeAssistant instance with cleanup. The cloud API is mocked by the tests. This suite checks coordinator/entity logic, home/module mapping, fallbacks, measurements and command error behavior. It does not load the full integration config flow, log into a real account or exercise a boiler. No claim of complete integration coverage is made.

Other old blueprint test modules still reference nonexistent integration APIs and are not part of the maintained suite. Running the entire tests directory is not the supported command.

The `hacs` branch builds one canonical source tree into two archives. The runner extracts each archive to a temporary `custom_components/<domain>` directory and uses a fresh interpreter for each package. The same maintained regression tests run against both packages, with only their import/path references adapted. Configuration-flow registration, platform imports and separate original/NG library classes after HA initializes are also checked; no account or real boiler is contacted. These checks do not establish full config-entry setup or registry/controls coexistence with the original integration.

Manual-distribution export checks use a synthetic local Git repository and run the generated verifier before/after hand edits and unexpected files. They also check provenance, dirty-tree labeling, unchanged license/code and refusal to overwrite existing output or add a second domain to the catalog source directory.
