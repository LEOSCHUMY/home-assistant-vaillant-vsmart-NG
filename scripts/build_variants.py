"""Build both integration domains from one source tree, without publishing."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

SOURCE_DOMAIN = "vaillant_vsmart_ng"
VARIANTS = {"hacs": "vaillant_vsmart_ng", "legacy": "vaillant_vsmart"}
ROOT = Path(__file__).resolve().parents[1]


def build_variants(source: Path, output: Path) -> dict:
    """Write deterministic archives and a checksum/identity report for both domains."""
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError("Output must be outside the integration source directory")
    files = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Integration source must not contain symbolic links")
        relative = path.relative_to(source)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            content = path.read_bytes()
            if path.suffix == ".py":
                ast.parse(content, filename=str(relative))
            files[relative.as_posix()] = content

    manifest = json.loads(files["manifest.json"])
    if manifest.get("domain") != SOURCE_DOMAIN:
        raise ValueError("Source manifest must use the canonical NG domain")
    report = {"version": manifest["version"], "variants": {}}
    output.mkdir(parents=True, exist_ok=True)
    for variant, domain in VARIANTS.items():
        variant_manifest = {**manifest, "domain": domain}
        archive = output / f"{domain}.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for name, content in sorted(files.items()):
                if name == "manifest.json":
                    content = (json.dumps(variant_manifest, indent=2) + "\n").encode()
                entry = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = ZIP_DEFLATED
                bundle.writestr(entry, content)
        report["variants"][variant] = {
            "domain": domain,
            "archive": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        }
    (output / "variants.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    """Build artifacts locally; never install, create releases or change source files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_variants(ROOT / "custom_components" / SOURCE_DOMAIN, args.output)


if __name__ == "__main__":
    main()
