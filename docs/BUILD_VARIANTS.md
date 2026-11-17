# One integration source, two domain variants

Status: **unreleased packaging foundation on branch `hacs`**. These artifacts are for review and isolated testing, not installation on a working Home Assistant system. Published integration `v0.1.2` and library `0.2.0` are unchanged.

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

CI runs both packages on HA 2024.5.0 / Python 3.12 and HA 2026.11.1 / Python 3.14. The manual release-preparation workflow can upload review artifacts but still does not create a tag, GitHub release, or production installation. The artifacts currently retain the existing source version; a new version will be selected separately before publication.

## One NG library for both variants

Both integration variants use the **same NG library development candidate** under the isolated import namespace `vaillant_netatmo_api_ng`. The library work branch is temporary preparation, not a second maintained library line. NG means **Next-Gen** in the public project name.

The manifest and test requirements now target **unpublished `vaillant-netatmo-api-ng==0.3.0.dev0`**. Development CI installs an exact candidate commit first, then resolves the HA environment. Do not install the generated archives on a working system: a normal HA dependency install cannot obtain this development candidate from PyPI. Replace the candidate source and development version with one published library release before production publication.

The library candidate is checked alongside upstream 0.13.1 for disjoint installed files and separate classes in both import orders. The integration package runner also imports both libraries after HA initializes its HTTP aliases. These checks establish package isolation, not a full original/NG config-entry setup, registry migration, real-account login, controls or rollback. Those remain release gates.

## Final documentation and distribution

The final public README should recommend the HACS/Marketplace variant first, with its icon and install button. It should link to a separate manual distribution repository for users who want to keep the existing integration domain and entity identifiers. That repository should hold the manual installation, update and rollback instructions and receive generated output from the same reviewed source; it must not become a second hand-maintained implementation.

The manual repository has not been created or selected, so no destination link or automated upload is configured. Creating/publishing that repository and changing release workflows remain explicit later steps. A catalog repository should expose one integration domain; two generated archives are not a promise that HACS offers a variant selector or automatically routes existing installations to the compatible artifact.

Keeping the old domain and current unique-ID logic is intended to preserve identities for the compatible variant. Verify config entries, devices, entity IDs, update ownership and rollback on a secondary installation before claiming that outcome generally. A new-domain installation is a separate setup, not an automatic migration of existing config entries.

## Remaining release gates

1. Review the isolated NG library candidate and its coexistence checks, select a stable version, and publish it through the normal approval process.
2. Point **both** integration variants at that one published library and run the isolated matrix again.
3. Test installation/configuration coexistence, config-entry identities, websocket registrations and available controls on a secondary HA instance; source/import checks alone are insufficient.
4. Create the manual distribution repository and its instructions; verify the compatible upgrade and restore path without rewriting private registry storage.
5. Finish the HACS-first README, icon/button and manual-repository link, validate packaging with HACS, then select a new release version.
6. Publish only after review and update the HACS submission with the released new-domain integration.

No production upgrade, private-storage edit, source-branch merge or release publication is authorized by running the local builder.
