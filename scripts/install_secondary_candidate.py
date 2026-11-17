"""Stage the pinned NG candidate on the disposable secondary HA instance only."""
import ast
import argparse
import hashlib
import io
import json
from email.parser import BytesParser
from importlib.metadata import distribution, version, PackageNotFoundError
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

INTEGRATION_COMMIT = "1d87afe740a00bbfbcf48c8b1a34a5bd761014e1"
LIBRARY_COMMIT = "eab91cbe180f86bc6b34355e4f30a08e26566fbf"
EXPECTED = {
    "__init__.py": "787cfad1ce10bae72b51cb8d7791ce7cf3b72d81",
    "boiler_status.py": "55e52612e29a1693ff1e64636928105d6b2c59fc",
    "brand/icon.png": "0ac5d0f1d0c8d3f5c70cf43bfb4d2e398438d3a7",
    "brand/icon@2x.png": "94b77d0d2f97efbc206121c5e1f2b309ff6821dc",
    "climate.py": "4110948b22ac79248e2226ca34f74078602f345c",
    "config_flow.py": "c8732c8ca895389789f931241ce474739613f77d",
    "const.py": "1b4915620db813af3f2b56bb33299f4ed9b0689d",
    "entity.py": "5ddb6dfe773a0208a538d51ffc5d7bdd1aedfc46",
    "manifest.json": "ded8c3e0a5a490e91523ae89ef082070749f321f",
    "number.py": "717311fb62532ee26bda2d59277e5daa62cbe556",
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


def fingerprint(directory):
    """Record code hashes only; never read HA account storage."""
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def install(config, wheel_sha):
    """Verify all inputs before adding one new integration directory."""
    if version("homeassistant") != "2026.11.1":
        raise ValueError("This field test targets HA 2026.11.1")
    if version("vaillant-netatmo-api") != "0.13.1":
        raise ValueError("The original library 0.13.1 must be installed")
    try:
        version("vaillant-netatmo-api-ng")
    except PackageNotFoundError:
        pass
    else:
        raise ValueError("An NG library is already installed; inspect it first")

    components = config / "custom_components"
    original = components / "vaillant_vsmart"
    target = components / "vaillant_vsmart_ng"
    if target.exists():
        raise ValueError("The NG directory already exists; nothing overwritten")
    old = json.loads((original / "manifest.json").read_text())
    if old.get("domain") != "vaillant_vsmart" or old.get("version") != "0.11.2":
        raise ValueError("Expected the configured original integration 0.11.2")
    before = fingerprint(original)

    state_dir = config / "vsmart-coexistence-test"
    wheel = state_dir / "library/vaillant_netatmo_api_ng-0.3.0.dev0-py3-none-any.whl"
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != wheel_sha:
        raise ValueError("Candidate wheel hash mismatch")
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(name.startswith("vaillant_netatmo_api/") for name in names):
            raise ValueError("Candidate wheel occupies the original import namespace")
        if "vaillant_netatmo_api_ng/__init__.py" not in names:
            raise ValueError("Candidate wheel has no isolated NG namespace")
        metadata = BytesParser().parsebytes(archive.read(
            "vaillant_netatmo_api_ng-0.3.0.dev0.dist-info/METADATA"
        ))
        if metadata["Name"] != "vaillant-netatmo-api-ng" or metadata["Version"] != "0.3.0.dev0":
            raise ValueError("Unexpected candidate wheel identity")

    url = ("https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/archive/"
           + INTEGRATION_COMMIT + ".zip")
    with urlopen(url, timeout=60) as response:
        content = response.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("Unexpected archive size")
    payload = {}
    with ZipFile(io.BytesIO(content)) as archive:
        prefix = archive.namelist()[0].split("/")[0] + "/custom_components/vaillant_vsmart_ng/"
        for name in archive.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix):]
            if relative not in EXPECTED or relative in payload:
                raise ValueError("Unexpected or duplicate candidate file")
            data = archive.read(name)
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if blob != EXPECTED[relative]:
                raise ValueError("Candidate file differs from the reviewed commit")
            if relative.endswith(".py"):
                ast.parse(data, filename=relative)
            payload[relative] = data
    if set(payload) != set(EXPECTED):
        raise ValueError("Candidate archive is incomplete")

    manifest = json.loads(payload["manifest.json"])
    if manifest["domain"] != "vaillant_vsmart_ng":
        raise ValueError("Candidate manifest has the wrong domain")
    if manifest["requirements"] != ["vaillant-netatmo-api-ng==0.3.0.dev0"]:
        raise ValueError("Unexpected candidate requirement")
    manifest["requirements"] = [f"vaillant-netatmo-api-ng @ {wheel.as_uri()}"]

    original_dist = distribution("vaillant-netatmo-api")
    library_hashes = {
        str(original_dist.locate_file(path)): hashlib.sha256(
            original_dist.locate_file(path).read_bytes()
        ).hexdigest()
        for path in original_dist.files
        if str(path).startswith("vaillant_netatmo_api/") and str(path).endswith(".py")
    }
    state = {
        "integration_commit": INTEGRATION_COMMIT,
        "library_commit": LIBRARY_COMMIT,
        "wheel_sha256": wheel_sha,
        "original_component_hashes": before,
        "original_library_hashes": library_hashes,
    }
    with TemporaryDirectory(prefix=".vsmart-ng-stage-", dir=components) as temporary:
        stage = Path(temporary) / "component"
        stage.mkdir()
        for relative, data in payload.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        if fingerprint(original) != before:
            raise ValueError("Original integration changed during staging")
        if target.exists():
            raise ValueError("NG directory appeared during staging")
        (state_dir / "verification.json").write_text(json.dumps(state, indent=2) + "\n")
        stage.rename(target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-sha256", required=True)
    install(Path("/config"), parser.parse_args().wheel_sha256)
    sys.stdout.write(
        "NG aggiunta: /config/custom_components/vaillant_vsmart_ng\n"
        "22 file verificati contro il commit testato.\n"
        "Manifest di prova impostato sulla wheel persistente.\n"
        "Originale invariata. Nessuna libreria installata da questo comando.\n"
    )

