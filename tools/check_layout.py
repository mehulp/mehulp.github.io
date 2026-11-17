"""Check that the repo layout exists and that generated/private paths are git-ignored."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_DIRS = [
    "content/about",
    "content/projects",
    "content/journal",
    "content/blog",
    "content/system-design",
    "tools",
    "site",
    ".github/workflows",
]

MUST_BE_IGNORED = [
    "private/test-note.md",
    "site/graph-data.js",
    "site/pages-data.js",
]


def missing_dirs(root, expected):
    """Return the folders in `expected` that do not exist under `root`."""
    return [d for d in expected if not (root / d).is_dir()]


def is_ignored(root, relative_path):
    """Ask git whether `relative_path` would be ignored. Return True or False."""
    result = subprocess.run(["git", "check-ignore", "-q", relative_path], cwd=root)
    if result.returncode == 128:
        raise RuntimeError("git could not answer. Is this folder a git repo?")
    return result.returncode == 0


def main():
    """Print one line per problem, then a summary. Return 0 if all good, else 1."""
    problems = 0
    for d in missing_dirs(ROOT, EXPECTED_DIRS):
        print(f"MISSING  folder {d}")
        problems += 1
    for p in MUST_BE_IGNORED:
        if is_ignored(ROOT, p):
            print(f"OK       ignored {p}")
        else:
            print(f"DANGER   not ignored {p}")
            problems += 1
    if problems == 0:
        print(f"All good: {len(EXPECTED_DIRS)} folders present, {len(MUST_BE_IGNORED)} paths ignored.")
        return 0
    print(f"{problems} problem(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
