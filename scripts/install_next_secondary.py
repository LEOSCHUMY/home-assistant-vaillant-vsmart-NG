"""Stage and verify the pinned next-release candidate on the disposable secondary."""
import argparse
import ast
import hashlib
import io
import json
from email.parser import BytesParser
from importlib.metadata import distribution, version
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

from packaging.requirements import Requirement

INTEGRATION_COMMIT = "3612e027e9c2bd3cc8c418142f2d132a358f2513"
LIBRARY_COMMIT = "ee8052845d8e838abe09c2a0d9fa5baaf046a0eb"
DOMAIN = "vaillant_vsmart_ng"
STATE_DIRECTORY = "vsmart-next-field-test"
EXPECTED = {
    "__init__.py": "8e0f3501071f7c3ae0feeac36f878263be188b14",
    "boiler_status.py": "55e52612e29a1693ff1e64636928105d6b2c59fc",
    "brand/icon.png": "0ac5d0f1d0c8d3f5c70cf43bfb4d2e398438d3a7",
    "brand/icon@2x.png": "94b77d0d2f97efbc206121c5e1f2b309ff6821dc",
    "climate.py": "4cdb0ac8ec57ece0c1504e56c76e02986fe7385b",
    "config_flow.py": "c8732c8ca895389789f931241ce474739613f77d",
    "const.py": "1b4915620db813af3f2b56bb33299f4ed9b0689d",
    "devices.py": "aa0edf5a5bc75708b46e18f42b553bb77cc2b03c",
    "entity.py": "fb2d61d2f6516cbde9c2697ba9a50a16da74fc93",
    "home_targeting.py": "55a692243d7388a383c950a49b211400aab9f70f",
    "manifest.json": "2b01449cfd24a707f52c396aa1d385547dcff0bc",
    "number.py": "717311fb62532ee26bda2d59277e5daa62cbe556",
    "room_setpoint.py": "d9a42b751858a41557ae3ca730d13e55b3fd1ac1",
    "room_temperature.py": "625928e12838449a338cffef7e96870d927b66e3",
    "schedule.py": "48bffb1e6e0994ecc2f3dd689dd59de1731f9e4e",
    "select.py": "d79719e851e15eca9fbcd639c3b94b0be290c27d",
    "sensor.py": "6bc52c2affd7466b37b65c1a966c951912e87f37",
    "switch.py": "7e387b7190d6270e580a3e4f98a84717bda2fb0e",
    "translations/en.json": "7987c03f2aa0f510788261b2ef964e1445003b9b",
    "translations/es.json": "4217c5e3dc2a4a90b34ce683405573d107f168d9",
    "translations/fr.json": "6b610308d18a7fde2224363c638c031dc78011bd",
    "translations/hr.json": "4ab333d97f27181c1e02298111602f4cfc6cc46c",
    "translations/pl.json": "e76e9f9a45bda6efcfbdb0ba3877131359c2b3e1",
    "water_heater.py": "8b29e7fd18f2b2c60f65281846523788a0779040",
    "websockets.py": "951a6a1449e235ce5659e3ff3c4bd2bf2a951c65"
}


def digest(value):
    """Hash registry identity without logging its identifiers or names."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def fingerprint(directory):
    """Hash component files, ignoring interpreter caches."""
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def original_library_hashes():
    """Hash only the original distribution's Python files."""
    dist = distribution("vaillant-netatmo-api")
    if not dist.files:
        raise ValueError("Original distribution has no installed file records")
    return {
        str(dist.locate_file(p)): hashlib.sha256(dist.locate_file(p).read_bytes()).hexdigest()
        for p in dist.files
        if str(p).startswith("vaillant_netatmo_api/") and str(p).endswith(".py")
    }


def registry_snapshot(config, domain):
    """Read registry identity only; never read core.config_entries or credentials."""
    entities = json.loads((config / ".storage/core.entity_registry").read_text())["data"]["entities"]
    devices = json.loads((config / ".storage/core.device_registry").read_text())["data"]["devices"]
    rows = [e for e in entities if e.get("platform") == domain]
    entry_ids = {e["config_entry_id"] for e in rows if e.get("config_entry_id")}
    owned = [d for d in devices if entry_ids.intersection(d.get("config_entries", []))]
    entity_ids = sorted(
        [{k: e.get(k) for k in ("entity_id", "unique_id", "config_entry_id", "device_id")}
         for e in rows], key=lambda e: e["entity_id"]
    )
    device_ids = sorted(
        [{"id": d["id"], "identifiers": sorted(d.get("identifiers", [])),
          "config_entries": sorted(d.get("config_entries", []))} for d in owned],
        key=lambda d: d["id"],
    )
    owned_ids = {d["id"] for d in owned}
    parents = [d.get("via_device_id") for d in owned if d.get("via_device_id")]
    return {
        "entity_count": len(rows),
        "device_count": len(owned),
        "entities_hash": digest(entity_ids),
        "devices_hash": digest(device_ids),
        "linked_modules": len(parents),
        "invalid_parent_links": sum(parent not in owned_ids for parent in parents),
    }


def validate_wheel(wheel, expected_sha):
    """Reject wrong wheel or incompatible dependencies without installing anything."""
    data = wheel.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError("Candidate wheel SHA256 mismatch")
    with ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        prefix = "vaillant_netatmo_api_ng-0.4.0.dev0.dist-info/"
        if len(names) != len(set(names)) or any(
            not n.startswith(("vaillant_netatmo_api_ng/", prefix)) or ".." in Path(n).parts
            for n in names
        ):
            raise ValueError("Unexpected candidate wheel files")
        metadata = BytesParser().parsebytes(archive.read(prefix + "METADATA"))
        if metadata["Name"] != "vaillant-netatmo-api-ng" or metadata["Version"] != "0.4.0.dev0":
            raise ValueError("Unexpected candidate wheel identity")
        dependencies = {}
        for raw in metadata.get_all("Requires-Dist", []):
            requirement = Requirement(raw)
            if requirement.marker and not requirement.marker.evaluate():
                continue
            installed = version(requirement.name)
            if installed not in requirement.specifier:
                raise ValueError(f"Incompatible installed dependency: {requirement.name}")
            dependencies[requirement.name] = installed
    return dependencies


def fetch_component():
    """Read only integration files matching the reviewed immutable Git blobs."""
    url = ("https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/archive/"
           + INTEGRATION_COMMIT + ".zip")
    with urlopen(url, timeout=60) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError("Unexpected source archive size")
    payload = {}
    with ZipFile(io.BytesIO(data)) as archive:
        root = archive.namelist()[0].split("/")[0]
        prefix = root + "/custom_components/" + DOMAIN + "/"
        for name in archive.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix):]
            if relative not in EXPECTED or relative in payload:
                raise ValueError("Unexpected or duplicate candidate integration file")
            content = archive.read(name)
            blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
            if blob != EXPECTED[relative]:
                raise ValueError("Integration differs from pinned source")
            if relative.endswith(".py"):
                ast.parse(content, filename=relative)
            payload[relative] = content
    if set(payload) != set(EXPECTED):
        raise ValueError("Incomplete integration archive")
    return payload


def stage(config, wheel_sha):
    """Replace only the already configured NG component, keeping the original intact."""
    if version("homeassistant") != "2026.11.1":
        raise ValueError("This secondary procedure targets HA 2026.11.1")
    if version("vaillant-netatmo-api") != "0.13.1":
        raise ValueError("Expected original library 0.13.1")
    if version("vaillant-netatmo-api-ng") != "0.3.0.dev0":
        raise ValueError("Expected the previous secondary NG candidate; inspect before updating")
    components = config / "custom_components"
    original = components / "vaillant_vsmart"
    target = components / DOMAIN
    old = json.loads((original / "manifest.json").read_text())
    current = json.loads((target / "manifest.json").read_text())
    if old.get("domain") != "vaillant_vsmart" or old.get("version") != "0.11.2":
        raise ValueError("Expected the configured original integration 0.11.2")
    if current.get("domain") != DOMAIN or current.get("version") != "0.1.2":
        raise ValueError("Expected the previous secondary NG component 0.1.2")
    state_dir = config / STATE_DIRECTORY
    state_path = state_dir / "verification.json"
    if state_path.exists():
        raise ValueError("A field-test baseline already exists; nothing overwritten")
    wheel = state_dir / "library/vaillant_netatmo_api_ng-0.4.0.dev0-py3-none-any.whl"
    dependencies = validate_wheel(wheel, wheel_sha)
    original_files = fingerprint(original)
    original_python = original_library_hashes()
    before_original = registry_snapshot(config, "vaillant_vsmart")
    before_ng = registry_snapshot(config, DOMAIN)
    if not all(s["entity_count"] and s["device_count"] for s in (before_original, before_ng)):
        raise ValueError("Both configured integrations must have registry entries")
    payload = fetch_component()
    manifest = json.loads(payload["manifest.json"])
    if (manifest.get("domain") != DOMAIN or manifest.get("version") != "0.2.1.dev0"
            or manifest.get("requirements") != ["vaillant-netatmo-api-ng==0.4.0.dev0"]):
        raise ValueError("Unexpected pinned candidate manifest")
    manifest["requirements"] = [f"vaillant-netatmo-api-ng @ {wheel.as_uri()}"]
    payload["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    state = {
        "integration_commit": INTEGRATION_COMMIT,
        "library_commit": LIBRARY_COMMIT,
        "wheel_sha256": wheel_sha,
        "dependencies": dependencies,
        "original_component_hashes": original_files,
        "original_library_hashes": original_python,
        "original_registry": before_original,
        "ng_registry": before_ng,
        "candidate_component_hashes": {p: hashlib.sha256(b).hexdigest() for p, b in payload.items()},
    }
    with TemporaryDirectory(prefix=".vsmart-next-stage-", dir=components) as temporary:
        temporary = Path(temporary)
        staged, previous = temporary / "new", temporary / "previous"
        staged.mkdir()
        for relative, content in payload.items():
            path = staged / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if fingerprint(original) != original_files or original_library_hashes() != original_python:
            raise ValueError("Original changed during preparation")
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        try:
            target.rename(previous)
            staged.rename(target)
        except BaseException:
            if previous.exists() and not target.exists():
                previous.rename(target)
            state_path.unlink(missing_ok=True)
            raise
    return state


def verify(config, fresh=False):
    """Verify installed code and registries after restart, without cloud requests."""
    state = json.loads((config / STATE_DIRECTORY / "verification.json").read_text())
    original = config / "custom_components/vaillant_vsmart"
    target = config / "custom_components" / DOMAIN
    if version("vaillant-netatmo-api-ng") != "0.4.0.dev0":
        raise ValueError("The installed NG library is not the candidate")
    if version("vaillant-netatmo-api") != "0.13.1":
        raise ValueError("The original library version changed")
    if fingerprint(original) != state["original_component_hashes"]:
        raise ValueError("Original integration files changed")
    if original_library_hashes() != state["original_library_hashes"]:
        raise ValueError("Original library Python files changed")
    if fingerprint(target) != state["candidate_component_hashes"]:
        raise ValueError("Candidate integration files changed")
    if registry_snapshot(config, "vaillant_vsmart") != state["original_registry"]:
        raise ValueError("Original registry identity or gateway links changed")
    now = registry_snapshot(config, DOMAIN)
    before = state["ng_registry"]
    keys = ("entity_count", "device_count") if fresh else (
        "entity_count", "device_count", "entities_hash", "devices_hash"
    )
    if any(now[k] != before[k] for k in keys):
        raise ValueError("NG registry differs from the expected upgrade/fresh-setup baseline")
    if now["invalid_parent_links"] or not now["linked_modules"]:
        raise ValueError("NG module is not linked to its own gateway")
    wheel = config / STATE_DIRECTORY / "library/vaillant_netatmo_api_ng-0.4.0.dev0-py3-none-any.whl"
    dependencies = validate_wheel(wheel, state["wheel_sha256"])
    if dependencies != state["dependencies"]:
        raise ValueError("Installed dependency versions changed; inspect before continuing")
    candidate = distribution("vaillant-netatmo-api-ng")
    with ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("vaillant_netatmo_api_ng/") and name.endswith(".py"):
                if candidate.locate_file(name).read_bytes() != archive.read(name):
                    raise ValueError("Installed NG library differs from candidate wheel")
    return now


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--wheel-sha256")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    config = Path("/config")
    if args.stage:
        if not args.wheel_sha256 or args.fresh:
            parser.error("--stage requires --wheel-sha256 and does not accept --fresh")
        result = stage(config, args.wheel_sha256)
        print("NG staged: 0.2.1.dev0; 25 files verified against pinned source.")
        print("Manifest points to the persistent 0.4.0.dev0 wheel.")
        print("Original component/library unchanged; registry identities recorded as hashes.")
        print("No library installed, no credentials/config entries read, no API calls made.")
    else:
        result = verify(config, fresh=args.fresh)
        print("Installed candidate code verified; original component/library/registry unchanged.")
        print("NG:", result["entity_count"], "entities,", result["device_count"], "devices.")
        print("Gateway links verified; dependency versions unchanged.")

