"""Verify the identity, reproducibility and isolation of the two release artifacts."""

import importlib.util
import json
from pathlib import Path
import struct
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_variants", ROOT / "scripts" / "build_variants.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_variants_share_code_but_keep_distinct_manifest_identities(tmp_path):
    """Only the manifest domain differs; both archives retain all Python and brand assets."""
    source = ROOT / "custom_components" / builder.SOURCE_DOMAIN
    report = builder.build_variants(source, tmp_path)
    manifests = []
    payloads = []
    for variant, domain in builder.VARIANTS.items():
        with ZipFile(tmp_path / report["variants"][variant]["archive"]) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            assert manifest.pop("domain") == domain
            manifests.append(manifest)
            files = {name: archive.read(name) for name in archive.namelist() if name != "manifest.json"}
            assert "__init__.py" in files
            assert all("__pycache__" not in name and not name.endswith(".pyc") for name in files)
            for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
                data = files[f"brand/{name}"]
                assert data[:8] == b"\x89PNG\r\n\x1a\n"
                assert struct.unpack(">II", data[16:24]) == (size, size)
            payloads.append(files)
    assert manifests[0] == manifests[1]
    assert payloads[0] == payloads[1]
    assert payloads[0]["entity.py"] == (source / "entity.py").read_bytes()


def test_archives_are_reproducible_and_do_not_change_source(tmp_path):
    """Repeated builds preserve hashes and never rewrite the canonical manifest."""
    source = ROOT / "custom_components" / builder.SOURCE_DOMAIN
    before = (source / "manifest.json").read_bytes()
    first = builder.build_variants(source, tmp_path / "first")
    second = builder.build_variants(source, tmp_path / "second")
    assert first == second
    assert (source / "manifest.json").read_bytes() == before


def test_reject_output_inside_source(tmp_path):
    """Prevent generated artifacts from becoming input on a later build."""
    with pytest.raises(ValueError, match="outside"):
        builder.build_variants(tmp_path, tmp_path / "build")


def test_reject_symlinks_outside_source(tmp_path):
    """Do not include files reached through symlinks in a release archive."""
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("must not be packaged")
    (source / "linked.txt").symlink_to(outside)
    with pytest.raises(ValueError, match="symbolic links"):
        builder.build_variants(source, tmp_path / "output")
