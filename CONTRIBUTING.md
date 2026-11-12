# Contributing

Thank you for your interest in contributing to **Vaillant vSMART for Home Assistant**.

This repository is an independently maintained continuation of the original
[Vaillant vSMART integration](https://github.com/MislavMandaric/home-assistant-vaillant-vsmart).
Bug reports, API research, documentation improvements, tests and code contributions
are welcome.

## Before opening a pull request

1. Check the [existing issues](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/issues)
   and pull requests to avoid duplicating work.
2. For substantial changes or new features, open an issue first so the proposed
   approach can be discussed.
3. Fork this repository and create your working branch from `dev`.
4. Keep changes focused and update documentation or tests when appropriate.
5. Never include account credentials, client secrets, access tokens or other
   personal information in code, issues, pull requests or logs.

Pull requests should target the `dev` branch. Please describe the motivation,
the behavior changed and any manual testing performed. Link related issues where
applicable.

## Development setup

The integration code lives in
`custom_components/vaillant_vsmart`. The repository also includes a development
configuration and helper scripts.

A typical local setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

To start the development Home Assistant instance using the repository's
configuration:

```bash
./scripts/develop
```

The script starts Home Assistant with `config/` as its configuration directory
and makes the repository's `custom_components/` directory available.

## Tests and code quality

Run the maintained regression suite locally with:

```bash
python3 -m pytest -q tests/test_regression_resilience.py tests/test_room_temperature.py tests/test_boiler_status.py
```

GitHub Actions runs these three modules using the Home Assistant and test-plugin versions pinned in `requirements.txt`. Older blueprint test modules still reference APIs that this integration does not expose; running the entire `tests/` directory is not the supported regression command.

The minimum version in `hacs.json` is an installation requirement. Before raising it, check the APIs and dependencies actually used. Before claiming compatibility, distinguish automated tests from real-installation observations; the current evidence is documented in the README.

Run the repository's lint check with:

```bash
ruff check .
```

The repository also includes a pre-commit configuration. If you use
[pre-commit](https://pre-commit.com/), you can install its hooks and run them
across the repository:

```bash
pre-commit install
pre-commit run --all-files
```

Please include or update automated tests for bug fixes and behavior changes
where practical. Do not describe a change as tested unless you have actually
run the relevant checks.

## Reporting bugs

Please use the
[GitHub issue tracker](https://github.com/LEOSCHUMY/home-assistant-vaillant-vsmart-NG/issues).
A useful report includes:

- Home Assistant version and installation type.
- Integration version or the commit/branch being tested.
- A concise description of the expected and actual behavior.
- Reproduction steps and relevant sanitized logs.

Remove usernames, passwords, client secrets, tokens, account identifiers and
other sensitive information before sharing diagnostics.

## Proposing changes

Keep pull requests focused and explain any user-visible impact, compatibility
considerations or migration steps. Changes affecting authentication, cloud API
requests, entity behavior or supported Home Assistant versions should include
tests where feasible.

This project is maintained by **LEOSCHUMY**. The maintainer may use
**ChatGPT (OpenAI) as an AI development assistant**; contributions and
publication decisions are reviewed and remain the responsibility of the human
maintainer.

## License

By submitting a contribution, you agree that it is distributed under the
project's [MIT License](LICENSE), consistent with the terms of that license.
