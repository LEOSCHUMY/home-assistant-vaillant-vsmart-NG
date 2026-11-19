# One integration source, two domain variants

Status: **integration 0.2.0 release preparation**. Artifacts built from a branch remain for review until a release is approved and published. Integration `v0.1.x` uses the older shared domain; 0.2.0 introduces the distinct HACS domain and requires published library `0.3.0`. A version in a manifest does not mean that a release exists.

## Build identities

| Variant | Installed directory | Manifest/runtime domain | Intended distribution |
| --- | --- | --- | --- |
| `hacs` | `custom_components/vaillant_vsmart_ng/` | `vaillant_vsmart_ng` | Recommended catalog version, after review and release |
| `legacy` | `custom_components/vaillant_vsmart/` | `vaillant_vsmart` | Separate manual distribution repository for existing NG installations |

The canonical source is `custom_components/vaillant_vsmart_ng/`. In `const.py`, `DOMAIN` is the final part of the installed package name. Both config flows and device/websocket registration use that constant. Home Assistant still requires the installed directory and `manifest.json` domain to agree; there is no runtime environment switch or user setting that changes an existing config entry's domain.

`scripts/build_variants.py` generates two deterministic archives with the same version and dependency requirements. Their integration Python, translations and brand files are byte-for-byte identical; only the manifest domain differs. Each archive has integration files at its root, suitable for extraction into its corresponding integration directory. The checksum report records which archive belongs to which domain.

```bash
python scripts/build_variants.py --output artifacts/variants
```

Output:

- `vaillant_vsmart_ng.zip`
- `vaillant_vsmart.zip`
- `variants.json` with version, domains, archive names and SHA-256 checksums

The builder does not modify source files, install anything, publish a release or choose a target repository. It rejects source symlinks and output inside the source directory, and excludes caches. Generation does not establish that an archive is ready for production use.

## Same tests, both packages

Use one of the isolated environments documented in [tests/README.md](../tests/README.md):

```bash
python -m pytest -q tests/test_build_variants.py
python scripts/test_variant.py --variant hacs --artifacts artifacts/variants
python scripts/test_variant.py --variant legacy --artifacts artifacts/variants
```

The runner extracts each archive into a temporary installation, then runs the same maintained regression tests and a separate platform/config-flow import check. Tests are adapted only for the selected import/path name; expected registry identifiers use the component's domain, while existing unique-ID expectations are preserved. Packaging tests check identical code/assets, distinct manifests, icon dimensions and reproducibility.

CI runs both packages on HA 2024.5.0 / Python 3.12 and HA 2026.11.1 / Python 3.14. The manual release-preparation workflow can upload review artifacts but still does not create a tag, GitHub release, or production installation. The artifacts now carry integration version **0.2.0** for both domains. The main repository release must contain only the new-domain integration; the compatible artifact belongs in its dedicated manual repository.

## One NG library for both variants

Both integration variants use the **same published NG library 0.3.0** under the isolated import namespace `vaillant_netatmo_api_ng`. There is one maintained NG library line for both domains. NG means **Next-Gen** in the public project name.

The manifest and test requirements target **published `vaillant-netatmo-api-ng==0.3.0`**. CI installs it normally from PyPI, without a candidate-source bootstrap, and the audit includes the library. Its stable wheel Python files match the development candidate used in the secondary test. Generated integration archives remain review artifacts until the integration release is approved and published.

The published library is checked alongside upstream 0.13.1 for disjoint installed files and separate classes in both import orders. The integration package runner also imports both libraries after HA initializes its HTTP aliases. These checks establish package isolation. The separate field report records initial original/NG configuration; it does not establish sustained polling, every control, registry migration or rollback. Keep those limitations explicit in release notes.

## Existing NG library compatibility

The successful side-by-side field test used the official original integration/library, which has a different distribution name. NG 0.1.2 and earlier instead depends on the same NG distribution name as the new library but imports the old namespace. Installing the new library without updating that old component would break its imports. Do not recommend new-domain installation alongside an unchanged older NG component. For continuity, update the old-domain component and library requirement together through the compatible variant, then keep both variants on the same new NG library version. That compatible upgrade remains unverified on the field.

## Final documentation and distribution

The final public README should recommend the HACS/Marketplace variant first, with its icon and install button. It should link to a separate manual distribution repository for users who want to keep the existing integration domain and entity identifiers. That repository should hold the manual installation, update and rollback instructions and receive generated output from the same reviewed source; it must not become a second hand-maintained implementation.

The manual distribution repository is [LEOSCHUMY/home-assistant-vaillant-vsmart-NG-manual](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG-manual), with default branch `main`. The main README links there for manual instructions. Its contents are generated review snapshots, not a published compatible release. No automated push is configured. The source [manual README template](../distribution/manual/README.md) contains the manual installation/update/rollback instructions and clearly labels current exports as development snapshots. The exporter creates the old-domain component, README, license, common changelog, Ko-fi funding file, generated-file verification workflow and provenance report. It deliberately omits `hacs.json`: the manual repository is not another catalog/custom-repository install route.

```bash
python scripts/export_manual_repository.py --output artifacts/manual-repository-preview
```

Use a new output directory: the exporter refuses to overwrite an existing one. It reads Git HEAD and records whether the source tree was modified, so a dirty local preview cannot be mistaken for an exact source-commit export. It never creates a GitHub repository, pushes commits, changes a Home Assistant installation or publishes a release. CI/manual preparation workflows upload a review artifact, including hidden funding/workflow files.

A catalog repository should expose one integration domain; two generated archives are not a promise that HACS offers a variant selector or automatically routes existing installations to the compatible artifact.

Keeping the old domain and current unique-ID logic is intended to preserve identities for the compatible variant. Verify config entries, devices, entity IDs, update ownership and rollback on a secondary installation before claiming that outcome generally. A new-domain installation is a separate setup, not an automatic migration of existing config entries.

## Remaining release gates

1. Completed: library 0.3.0 was reviewed, merged and published on PyPI and GitHub.
2. Completed for the dependency adoption: both variants require published library 0.3.0 and passed the isolated minimum/current HA matrix. Rerun checks on the final version/documentation commit before merge.
3. Initial new-domain/original configuration coexistence was verified on the secondary instance; see [the report](COEXISTENCE_TEST.md). Prolonged polling and new transitions were skipped. Every-control and identity/rollback coverage must not be inferred from that observation.
4. Maintain the manual distribution repository using the exporter/template and publish a compatible release only after review. Compatible upgrade/restore remain unverified; retain that limitation in the instructions.
5. The HACS-first README now includes the icon/install button. Its compatibility link now points to the manual repository. The library pins now use the published version and integration version 0.2.0 is selected. HACS and Hassfest checks must remain green on the reviewed release commit.
6. Publish only after review and update the HACS submission with the released new-domain integration.

No production upgrade, private-storage edit, source-branch merge or release publication is authorized by running the local builder.
