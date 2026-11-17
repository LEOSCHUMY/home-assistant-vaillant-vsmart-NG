"""Run the same regression tests and import checks against one built archive."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from build_variants import VARIANTS

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "test_regression_resilience.py",
    "test_room_temperature.py",
    "test_boiler_status.py",
)


def main() -> None:
    """Test extracted packages in isolation, without importing the checkout's component."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    domain = VARIANTS[args.variant]
    with TemporaryDirectory(prefix="vsmart-variant-") as temporary:
        workspace = Path(temporary)
        components = workspace / "custom_components"
        component = components / domain
        component.mkdir(parents=True)
        (components / "__init__.py").write_text("", encoding="utf-8")
        with ZipFile(args.artifacts / f"{domain}.zip") as archive:
            for name in archive.namelist():
                destination = (component / name).resolve()
                if not destination.is_relative_to(component.resolve()):
                    raise ValueError("Archive contains a path outside the integration")
            archive.extractall(component)
        manifest = json.loads((component / "manifest.json").read_text())
        if manifest["domain"] != domain:
            raise ValueError("Archive manifest does not match the selected domain")

        tests = workspace / "tests"
        tests.mkdir()
        for name in ("__init__.py", "conftest.py", *TESTS):
            content = (ROOT / "tests" / name).read_text(encoding="utf-8")
            # Tests share one source too; only their integration import/path changes.
            content = content.replace("vaillant_vsmart_ng", domain)
            (tests / name).write_text(content, encoding="utf-8")
        shutil.copyfile(ROOT / "pytest.ini", workspace / "pytest.ini")
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *(f"tests/{name}" for name in TESTS)],
            cwd=workspace, check=True,
        )
        # Fresh interpreter: HA must initialize its HTTP client aliases before imports.
        subprocess.run(
            [sys.executable, "-c", "\n".join([
                "import homeassistant",
                "from importlib import import_module",
                "from homeassistant import config_entries",
                f"domain = {domain!r}",
                'package = f"custom_components.{domain}"',
                'old_api = import_module("vaillant_netatmo_api")',
                'ng_api = import_module("vaillant_netatmo_api_ng")',
                'assert old_api.ThermostatClient is not ng_api.ThermostatClient',
                'assert old_api.Token is not ng_api.Token',
                'assert hasattr(ng_api.ThermostatClient, "async_get_home_status_snapshot")',
                'assert import_module(f"{package}.const").DOMAIN == domain',
                'import_module(f"{package}.config_flow")',
                'assert config_entries.HANDLERS.get(domain) is not None',
                'for platform in ("climate", "water_heater", "number", "select", "sensor", "switch", "websockets"):',
                '    import_module(f"{package}.{platform}")',
            ])],
            cwd=workspace, check=True,
        )


if __name__ == "__main__":
    main()
