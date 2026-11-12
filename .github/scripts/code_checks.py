"""Skip expensive code checks only for a known set of documentation files.

Unknown events, missing history, and Git errors always run the checks.
Rename detection is disabled so both the old and new paths are considered.
"""

import os
from pathlib import Path
import re
import subprocess

DOCUMENTATION = {
    b"README.md",
    b"CHANGELOG.md",
    b"CONTRIBUTING.md",
    b"MIGRATION.md",
    b"info.md",
}


def needs_checks(event, base, head):
    """Compare the entire PR or push; keep checking when detection is uncertain."""
    if event not in {"pull_request", "push"}:
        return True
    if not all(re.fullmatch(r"[0-9a-f]{40}", sha or "") for sha in (base, head)):
        return True
    if base == "0" * 40:
        return True
    comparison = f"{base}...{head}" if event == "pull_request" else f"{base}..{head}"
    try:
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "--no-renames", "-z", comparison],
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return True
    paths = [path for path in changed.split(b"\0") if path]
    return not paths or any(path not in DOCUMENTATION for path in paths)


if __name__ == "__main__":
    run = needs_checks(
        os.environ.get("EVENT_NAME"),
        os.environ.get("BASE_SHA"),
        os.environ.get("HEAD_SHA"),
    )
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"run={str(run).lower()}\n")
    print("Code checks required" if run else "Documentation only: skipping code checks")
