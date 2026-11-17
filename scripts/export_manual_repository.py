"""Export a review-only manual repository from the canonical Next-Gen source."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from build_variants import ROOT, SOURCE_DOMAIN, build_variants

SOURCE_REPOSITORY = "LEOSCHUMY/home-assistant-vaillant-vsmart-NG"
VERIFY_WORKFLOW = '''name: Verify generated distribution
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - name: Verify manifest and generated file hashes
        run: |
          python3 - <<'PY'
          import hashlib
          import json
          from pathlib import Path

          report = json.loads(Path("distribution.json").read_text())
          assert report["domain"] == "vaillant_vsmart"
          manifest = json.loads(Path("custom_components/vaillant_vsmart/manifest.json").read_text())
          assert manifest["domain"] == report["domain"]
          assert manifest["version"] == report["version"]
          assert manifest["requirements"] == report["requirements"]
          actual = {
              path.as_posix() for path in Path(".").rglob("*")
              if path.is_file() and ".git" not in path.parts
              and "__pycache__" not in path.parts and path.suffix != ".pyc"
          }
          assert actual == set(report["files_sha256"]) | {"distribution.json"}
          for name, digest in report["files_sha256"].items():
              path = Path(name)
              assert not path.is_absolute() and ".." not in path.parts
              assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
          PY
'''


def export_manual_repository(root: Path, output: Path) -> dict:
    """Generate code and documentation without writing to GitHub or an HA config."""
    if output.exists():
        raise ValueError("Output already exists; existing repository content is never overwritten")
    if output.resolve().is_relative_to((root / "custom_components").resolve()):
        raise ValueError("Output must be outside custom_components")
    source_commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
    ).strip()
    dirty = bool(subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=normal"], text=True,
    ).strip())
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="vsmart-manual-export-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        packages = temporary / "packages"
        variants = build_variants(root / "custom_components" / SOURCE_DOMAIN, packages)
        stage = temporary / "repository"
        component = stage / "custom_components/vaillant_vsmart"
        component.mkdir(parents=True)
        with ZipFile(packages / variants["variants"]["legacy"]["archive"]) as archive:
            for name in archive.namelist():
                if not (component / name).resolve().is_relative_to(component.resolve()):
                    raise ValueError("Unexpected integration archive path")
                path = component / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))
        manifest = json.loads((component / "manifest.json").read_text())
        readme = (root / "distribution/manual/README.md").read_text(encoding="utf-8")
        readme = readme.replace("@@SOURCE_COMMIT@@", source_commit)
        readme = readme.replace("@@SOURCE_DIRTY@@", "yes" if dirty else "no")
        readme = readme.replace("@@VERSION@@", manifest["version"])
        (stage / "README.md").write_text(readme, encoding="utf-8")
        for name in ("LICENSE", "CHANGELOG.md"):
            shutil.copyfile(root / name, stage / name)
        (stage / ".github/workflows").mkdir(parents=True)
        shutil.copyfile(root / ".github/FUNDING.yml", stage / ".github/FUNDING.yml")
        (stage / ".github/workflows/verify.yml").write_text(VERIFY_WORKFLOW, encoding="utf-8")
        (stage / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        report = {
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": source_commit,
            "source_dirty": dirty,
            "status": "review_only_not_published",
            "domain": "vaillant_vsmart",
            "version": manifest["version"],
            "requirements": manifest["requirements"],
            "files_sha256": {
                path.relative_to(stage).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(stage.rglob("*")) if path.is_file()
            },
        }
        (stage / "distribution.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
    return report


def main() -> None:
    """Prepare a review directory; never create repositories, push commits or publish."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_manual_repository(ROOT, args.output)


if __name__ == "__main__":
    main()
