"""Check secondary staging boundaries with synthetic files, registries and wheels."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "next_secondary", ROOT / "scripts/install_next_secondary.py"
)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


@pytest.fixture
def secondary(tmp_path, monkeypatch):
    config = tmp_path / "config"
    components = config / "custom_components"
    old, ng = components / "vaillant_vsmart", components / installer.DOMAIN
    old.mkdir(parents=True)
    ng.mkdir()
    (old / "manifest.json").write_text(json.dumps(
        {"domain": "vaillant_vsmart", "version": "0.11.2"}
    ))
    (old / "__init__.py").write_text("# original\n")
    (ng / "manifest.json").write_text(json.dumps(
        {"domain": installer.DOMAIN, "version": "0.1.2"}
    ))
    (ng / "stale.py").write_text("# previous NG file\n")
    storage = config / ".storage"
    storage.mkdir()
    (storage / "core.config_entries").write_text("DO NOT READ CREDENTIAL STORAGE")
    entities = [
        {"platform": domain, "entity_id": "sensor." + suffix, "unique_id": suffix,
         "config_entry_id": suffix, "device_id": suffix + "-module"}
        for domain, suffix in [("vaillant_vsmart", "old"), (installer.DOMAIN, "ng")]
    ]
    devices = []
    for suffix in ("old", "ng"):
        for role in ("gateway", "module"):
            devices.append({
                "id": suffix + "-" + role, "config_entries": [suffix],
                "identifiers": [[suffix, role]],
                "via_device_id": suffix + "-gateway" if role == "module" else None,
            })
    (storage / "core.entity_registry").write_text(json.dumps({"data": {"entities": entities}}))
    (storage / "core.device_registry").write_text(json.dumps({"data": {"devices": devices}}))
    library_file = tmp_path / "original.py"
    library_file.write_text("# original library\n")
    monkeypatch.setattr(installer, "original_library_hashes", lambda: {
        str(library_file): hashlib.sha256(library_file.read_bytes()).hexdigest()
    })
    versions = {
        "homeassistant": "2026.11.1", "vaillant-netatmo-api": "0.13.1",
        "vaillant-netatmo-api-ng": "0.3.0.dev0", "idna": "3.20",
    }
    monkeypatch.setattr(installer, "version", lambda name: versions[name])
    installed = tmp_path / "installed"
    (installed / "vaillant_netatmo_api_ng").mkdir(parents=True)
    (installed / "vaillant_netatmo_api_ng/__init__.py").write_text("VALUE = 1\n")
    monkeypatch.setattr(installer, "distribution", lambda name: SimpleNamespace(
        locate_file=lambda path: installed / path
    ))
    wheel = config / installer.STATE_DIRECTORY / "library/vaillant_netatmo_api_ng-0.4.0.dev0-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    with ZipFile(wheel, "w") as archive:
        archive.writestr("vaillant_netatmo_api_ng/__init__.py", "VALUE = 1\n")
        archive.writestr("vaillant_netatmo_api_ng-0.4.0.dev0.dist-info/METADATA",
                         "Name: vaillant-netatmo-api-ng\nVersion: 0.4.0.dev0\nRequires-Dist: idna>=3\n")
    payload = {
        "__init__.py": b"# new NG\n",
        "manifest.json": json.dumps({
            "domain": installer.DOMAIN, "version": "0.2.1.dev0",
            "requirements": ["vaillant-netatmo-api-ng==0.4.0.dev0"],
        }).encode(),
    }
    monkeypatch.setattr(installer, "EXPECTED", {
        name: hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        for name, data in payload.items()
    })
    stream = io.BytesIO()
    with ZipFile(stream, "w") as archive:
        for name, data in payload.items():
            archive.writestr("repo/custom_components/" + installer.DOMAIN + "/" + name, data)
    monkeypatch.setattr(installer, "urlopen",
                        lambda *args, **kwargs: io.BytesIO(stream.getvalue()))
    return SimpleNamespace(config=config, old=old, ng=ng, versions=versions,
                           library_file=library_file,
                           sha=hashlib.sha256(wheel.read_bytes()).hexdigest())


def test_stage_preserves_original_and_registries_without_installing(secondary):
    s = secondary
    before = installer.fingerprint(s.old)
    registry = (s.config / ".storage/core.entity_registry").read_bytes()
    installer.stage(s.config, s.sha)
    assert installer.fingerprint(s.old) == before
    assert (s.config / ".storage/core.entity_registry").read_bytes() == registry
    assert s.library_file.read_text() == "# original library\n"
    assert s.versions["vaillant-netatmo-api-ng"] == "0.3.0.dev0"
    assert not (s.ng / "stale.py").exists()
    manifest = json.loads((s.ng / "manifest.json").read_text())
    assert manifest["version"] == "0.2.1.dev0"
    assert manifest["requirements"][0].startswith("vaillant-netatmo-api-ng @ file://")
    assert (s.config / ".storage/core.config_entries").read_text() == "DO NOT READ CREDENTIAL STORAGE"


def test_wrong_wheel_leaves_existing_ng_untouched(secondary):
    before = installer.fingerprint(secondary.ng)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        installer.stage(secondary.config, "0" * 64)
    assert installer.fingerprint(secondary.ng) == before
    assert not (secondary.config / installer.STATE_DIRECTORY / "verification.json").exists()


def test_unexpected_secondary_version_is_rejected(secondary):
    secondary.versions["vaillant-netatmo-api-ng"] = "0.3.0"
    before = installer.fingerprint(secondary.ng)
    with pytest.raises(ValueError, match="previous secondary"):
        installer.stage(secondary.config, secondary.sha)
    assert installer.fingerprint(secondary.ng) == before


def test_changed_source_is_rejected_before_staging(secondary, monkeypatch):
    monkeypatch.setitem(installer.EXPECTED, "__init__.py", "0" * 40)
    before = installer.fingerprint(secondary.ng)
    with pytest.raises(ValueError, match="differs from pinned"):
        installer.stage(secondary.config, secondary.sha)
    assert installer.fingerprint(secondary.ng) == before


def test_repeat_stage_never_overwrites_baseline(secondary):
    installer.stage(secondary.config, secondary.sha)
    before = installer.fingerprint(secondary.ng)
    with pytest.raises(ValueError, match="Expected the previous secondary NG component"):
        installer.stage(secondary.config, secondary.sha)
    assert installer.fingerprint(secondary.ng) == before


def test_failed_replacement_restores_previous_ng(secondary, monkeypatch):
    before = installer.fingerprint(secondary.ng)
    real_rename = Path.rename

    def fail_new(self, target):
        if self.name == "new":
            raise OSError("simulated replacement failure")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_new)
    with pytest.raises(OSError, match="simulated"):
        installer.stage(secondary.config, secondary.sha)
    assert installer.fingerprint(secondary.ng) == before
    assert not (secondary.config / installer.STATE_DIRECTORY / "verification.json").exists()


def test_verify_accepts_unchanged_upgrade_identity(secondary):
    installer.stage(secondary.config, secondary.sha)
    secondary.versions["vaillant-netatmo-api-ng"] = "0.4.0.dev0"
    result = installer.verify(secondary.config)
    assert result["entity_count"] == 1 and result["device_count"] == 2
    assert result["linked_modules"] == 1


def test_verify_detects_entity_identity_change_but_fresh_setup_allows_it(secondary):
    installer.stage(secondary.config, secondary.sha)
    secondary.versions["vaillant-netatmo-api-ng"] = "0.4.0.dev0"
    path = secondary.config / ".storage/core.entity_registry"
    data = json.loads(path.read_text())
    data["data"]["entities"][1]["entity_id"] = "sensor.new_ng_name"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="NG registry differs"):
        installer.verify(secondary.config)
    assert installer.verify(secondary.config, fresh=True)["entity_count"] == 1


def test_verify_detects_original_code_change(secondary):
    installer.stage(secondary.config, secondary.sha)
    secondary.versions["vaillant-netatmo-api-ng"] = "0.4.0.dev0"
    (secondary.old / "__init__.py").write_text("# unexpectedly modified\n")
    with pytest.raises(ValueError, match="Original integration files changed"):
        installer.verify(secondary.config)


def test_verify_detects_dependency_changes(secondary):
    installer.stage(secondary.config, secondary.sha)
    secondary.versions["vaillant-netatmo-api-ng"] = "0.4.0.dev0"
    secondary.versions["idna"] = "3.21"
    with pytest.raises(ValueError, match="dependency versions changed"):
        installer.verify(secondary.config)

