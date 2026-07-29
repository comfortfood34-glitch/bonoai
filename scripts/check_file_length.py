#!/usr/bin/env python3
"""Fail when a tracked, reviewable text file exceeds 300 lines."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_LINES = 300

# Lock files are machine-generated and may legitimately be large.
EXEMPT_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
}

# Generated data and captured fixtures are reviewed through their producers,
# schemas and tests. Exemptions are path-scoped instead of extension-wide.
EXEMPT_PATH_PREFIXES = (
    PurePosixPath("data/raw"),
    PurePosixPath("data/processed"),
    PurePosixPath("tests/fixtures"),
)


def _tracked_files() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return tuple(
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    )


def _is_exempt(path: str) -> bool:
    candidate = PurePosixPath(path)
    if candidate.name in EXEMPT_NAMES:
        return True
    return any(
        candidate == prefix or prefix in candidate.parents
        for prefix in EXEMPT_PATH_PREFIXES
    )


def _line_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="strict") as stream:
            return sum(1 for _ in stream)
    except UnicodeDecodeError:
        return None
    except OSError as error:
        raise RuntimeError(f"could not inspect tracked file {path}") from error


def check_all_files() -> tuple[tuple[str, int], ...]:
    violations: list[tuple[str, int]] = []
    for tracked_path in _tracked_files():
        if _is_exempt(tracked_path):
            continue
        path = Path(tracked_path)
        if not path.is_file():
            continue
        line_count = _line_count(path)
        if line_count is not None and line_count > MAX_LINES:
            violations.append((tracked_path, line_count))
    return tuple(sorted(violations, key=lambda item: (-item[1], item[0])))


def main() -> int:
    violations = check_all_files()
    if not violations:
        print(f"[file-length-guard] OK: no tracked file exceeds {MAX_LINES} lines")
        return 0

    print(
        f"[file-length-guard] FAILED: {len(violations)} tracked file(s) "
        f"exceed {MAX_LINES} lines"
    )
    for path, line_count in violations:
        print(f"  {path}: {line_count} lines (+{line_count - MAX_LINES})")
    print(
        "Split the file into focused modules. Add a legitimate exemption "
        "only in a separate, explicitly justified pull request."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
