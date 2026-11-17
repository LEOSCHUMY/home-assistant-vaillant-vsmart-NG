"""Exercise secondary-only staging offline with synthetic configuration and wheels."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "install_secondary_candidate", ROOT / "scripts" / "install_secondary_candidate.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """Create only fake code/manifest data; never inspect a real HA config directory."""
    config = tmp_path / "config"
    original = config / "custom_components/vaillant_vsmart"
    original.mkdir(parents=True)
    (original / "manifest.json").write_text(json.dumps({
        "domain": "vaillant_vsmart", "version": "0.11.2",
    }))
    (original / "__init__.py").write_text("# original code\n")
    old_library = tmp_path / "original.py"
    old_library.write_text("# original library\n")

    def installed_version(name):
        """Expose only the original and targeted HA baseline."""
        if name == "vaillant-netatmo-api-ng":
            raise installer.PackageNotFoundError(name)
        return {"homeassistant": "2026.11.1", "vaillant-netatmo-api": "0.13.1"}[name]

    monkeypatch.setattr(installer, "version", installed_version)
    monkeypatch.setattr(installer, "distribution", lambda name: SimpleNamespace(
        files=[Path("vaillant_netatmo_api/__init__.py")],
        locate_file=lambda path: old_library,
    ))
    wheel = config / "vsmart-coexistence-test/library/vaillant_netatmo_api_ng-0.3.0.dev0-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    with ZipFile(wheel, "w") as archive:
        archive.writestr("vaillant_netatmo_api_ng/__init__.py", "# NG library\n")
        archive.writestr("vaillant_netatmo_api_ng-0.3.0.dev0.dist-info/METADATA",
                         "Name: vaillant-netatmo-api-ng\nVersion: 0.3.0.dev0\n")
    payload = {
        "__init__.py": b"# NG integration\n",
        "manifest.json": json.dumps({
            "domain": "vaillant_vsmart_ng", "version": "0.1.2",
            "requirements": ["vaillant-netatmo-api-ng==0.3.0.dev0"],
        }).encode(),
    }
    monkeypatch.setattr(installer, "EXPECTED", {
        name: hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        for name, data in payload.items()
    })
    stream = io.BytesIO()
    with ZipFile(stream, "w") as archive:
        for name, data in payload.items():
            archive.writestr("repo/custom_components/vaillant_vsmart_ng/" + name, data)
    monkeypatch.setattr(installer, "urlopen", lambda *args, **kwargs: io.BytesIO(stream.getvalue()))
    return config, hashlib.sha256(wheel.read_bytes()).hexdigest(), original, old_library


def test_stages_only_new_domain_and_records_integrity_without_installing(setup):
    """Preserve both original code trees and persist only the NG manifest override."""
    config, sha, original, old_library = setup
    before = installer.fingerprint(original)
    installer.install(config, sha)
    assert installer.fingerprint(original) == before
    assert old_library.read_text() == "# original library\n"
    target = config / "custom_components/vaillant_vsmart_ng"
    manifest = json.loads((target / "manifest.json").read_text())
    wheel = config / "vsmart-coexistence-test/library/vaillant_netatmo_api_ng-0.3.0.dev0-py3-none-any.whl"
    assert manifest["requirements"] == [f"vaillant-netatmo-api-ng @ {wheel.as_uri()}"]
    state = json.loads((config / "vsmart-coexistence-test/verification.json").read_text())
    assert state["original_component_hashes"] == before
    assert len(state["original_library_hashes"]) == 1


def test_refuses_wrong_wheel_before_creating_integration(setup):
    """A stale or altered wheel must not result in partial installation."""
    config, _, original, _ = setup
    before = installer.fingerprint(original)
    with pytest.raises(ValueError, match="wheel hash mismatch"):
        installer.install(config, "wrong")
    assert not (config / "custom_components/vaillant_vsmart_ng").exists()
    assert installer.fingerprint(original) == before


def test_refuses_candidate_file_mismatch_before_creating_integration(setup, monkeypatch):
    """An archive changed from the pinned commit cannot be installed."""
    config, sha, original, _ = setup
    monkeypatch.setitem(installer.EXPECTED, "__init__.py", "0" * 40)
    with pytest.raises(ValueError, match="differs from the reviewed commit"):
        installer.install(config, sha)
    assert not (config / "custom_components/vaillant_vsmart_ng").exists()
    assert (original / "manifest.json").is_file()


def test_refuses_to_overwrite_existing_ng(setup):
    """A repeated command must not replace an existing candidate installation."""
    config, sha, _, _ = setup
    installer.install(config, sha)
    target = config / "custom_components/vaillant_vsmart_ng"
    before = installer.fingerprint(target)
    with pytest.raises(ValueError, match="already exists"):
        installer.install(config, sha)
    assert installer.fingerprint(target) == before
