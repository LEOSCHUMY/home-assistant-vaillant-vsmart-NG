"""Validate the generated manual repository and its independent integrity check."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "export_manual_repository", ROOT / "scripts/export_manual_repository.py"
)
exporter = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "scripts"))
spec.loader.exec_module(exporter)
sys.path.pop(0)


@pytest.fixture
def source(tmp_path):
    """Commit a synthetic source project; never push or change a real repository."""
    root = tmp_path / "source"
    component = root / "custom_components/vaillant_vsmart_ng"
    component.mkdir(parents=True)
    (component / "__init__.py").write_text("# shared implementation\n")
    (component / "manifest.json").write_text(json.dumps({
        "domain": "vaillant_vsmart_ng", "version": "0.1.2",
        "requirements": ["vaillant-netatmo-api-ng==0.3.0.dev0"],
    }))
    template = root / "distribution/manual/README.md"
    template.parent.mkdir(parents=True)
    template.write_text("Source @@SOURCE_COMMIT@@; dirty @@SOURCE_DIRTY@@; version @@VERSION@@\n")
    (root / "LICENSE").write_text("original attribution retained\n")
    (root / "CHANGELOG.md").write_text("# Shared changelog\n")
    (root / ".github").mkdir()
    (root / ".github/FUNDING.yml").write_text("ko_fi: LEOSCHUMY\n")
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run([
        "git", "-C", str(root), "-c", "user.name=Build test",
        "-c", "user.email=build@example.invalid", "commit", "--quiet", "-m", "fixture",
    ], check=True)
    return root


def test_export_preserves_shared_code_and_reports_exact_source(source, tmp_path):
    """A manual snapshot retains the canonical code and records identity and file hashes."""
    output = tmp_path / "manual"
    report = exporter.export_manual_repository(source, output)
    assert report["source_dirty"] is False
    assert report["status"] == "review_only_not_published"
    assert report["domain"] == "vaillant_vsmart"
    assert not (output / "hacs.json").exists()
    assert not (output / "custom_components/vaillant_vsmart_ng").exists()
    assert (output / "custom_components/vaillant_vsmart/__init__.py").read_bytes() == (
        source / "custom_components/vaillant_vsmart_ng/__init__.py"
    ).read_bytes()
    assert (output / "LICENSE").read_bytes() == (source / "LICENSE").read_bytes()
    assert "@@" not in (output / "README.md").read_text()
    assert report["source_commit"] in (output / "README.md").read_text()
    for name, digest in report["files_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("change", ["edit", "extra"])
def test_generated_ci_detects_modified_component(source, tmp_path, change):
    """Run the generated verifier, then reject a hand edit or an unrecorded file."""
    output = tmp_path / "manual"
    exporter.export_manual_repository(source, output)
    workflow = yaml.load((output / ".github/workflows/verify.yml").read_text(), Loader=yaml.BaseLoader)
    command = workflow["jobs"]["verify"]["steps"][1]["run"]
    verifier = "\n".join(command.splitlines()[1:-1])
    subprocess.run([sys.executable, "-c", verifier], cwd=output, check=True)
    name = "__init__.py" if change == "edit" else "extra.py"
    (output / "custom_components/vaillant_vsmart" / name).write_text("# edited\n")
    result = subprocess.run([sys.executable, "-c", verifier], cwd=output, capture_output=True)
    assert result.returncode != 0


def test_dirty_source_is_explicitly_reported(source, tmp_path):
    """Never describe uncommitted preview changes as an exact source commit."""
    (source / "custom_components/vaillant_vsmart_ng/__init__.py").write_text("# local edit\n")
    report = exporter.export_manual_repository(source, tmp_path / "manual")
    assert report["source_dirty"] is True
    assert "dirty yes" in (tmp_path / "manual/README.md").read_text()


def test_export_refuses_existing_repository_content(source, tmp_path):
    """A new export must not delete or overwrite an existing output repository."""
    output = tmp_path / "manual"
    output.mkdir()
    marker = output / "README.md"
    marker.write_text("existing repository\n")
    with pytest.raises(ValueError, match="already exists"):
        exporter.export_manual_repository(source, output)
    assert marker.read_text() == "existing repository\n"


def test_export_cannot_add_second_integration_to_canonical_tree(source):
    """Prevent placing the compatibility distribution under the catalog source folder."""
    output = source / "custom_components/manual"
    with pytest.raises(ValueError, match="outside custom_components"):
        exporter.export_manual_repository(source, output)
    assert not output.exists()
