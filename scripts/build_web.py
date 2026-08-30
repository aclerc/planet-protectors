"""Stage the game into a clean directory, then build the browser version with pygbag.

This wrapper exists because a bare `pygbag main.py` gets two things wrong in this repo:

1. pygbag bundles every file in the directory holding `main.py`. Run against the repository
   root it sweeps up `.venv` and the tool caches, and fails on media files inside pygame's
   own test fixtures. Staging copies out just the entry point and the game package.

2. pygbag decides which WASM modules to fetch by parsing `main.py` alone. A dependency
   imported only inside the package is never fetched, and the browser build then shows a
   blank canvas with no error anywhere the browser console can see it. `check_preloads`
   turns that silent failure into a build error naming the missing module.
"""

import ast
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
PACKAGE_NAME = "planet_protectors"
PACKAGE_DIR = REPO_ROOT / "src" / PACKAGE_NAME
ENTRY_POINT = REPO_ROOT / "main.py"
STAGE_DIR = REPO_ROOT / "build" / PACKAGE_NAME  # pygbag names the game after this directory


def top_level_imports(source: str, *, filename: str = "<string>") -> set[str]:
    """Return the top-level package names imported by a module's source."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source, filename)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def missing_preloads(entry_source: str, *, package_sources: Iterable[str]) -> set[str]:
    """Return third-party modules the package imports that the entry point does not name."""

    def third_party(names: set[str]) -> set[str]:
        return {n for n in names if n not in sys.stdlib_module_names and n != PACKAGE_NAME}

    needed: set[str] = set()
    for source in package_sources:
        needed |= third_party(top_level_imports(source))
    return needed - third_party(top_level_imports(entry_source))


def check_preloads() -> None:
    """Raise if the package needs a module the entry point does not import."""
    missing = missing_preloads(
        ENTRY_POINT.read_text(),
        package_sources=[path.read_text() for path in sorted(PACKAGE_DIR.rglob("*.py"))],
    )
    if missing:
        listed = ", ".join(sorted(missing))
        msg = (
            f"main.py must import {listed} for the browser build to work.\n"
            "pygbag parses only main.py to decide which WASM modules to fetch, so a module "
            "imported solely inside the package is never loaded and the game renders a blank "
            "canvas with no error in the browser console."
        )
        raise SystemExit(msg)


def stage_game() -> Path:
    """Copy the entry point and the game package into a clean staging directory."""
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True)
    shutil.copy(ENTRY_POINT, STAGE_DIR / "main.py")
    shutil.copytree(PACKAGE_DIR, STAGE_DIR / PACKAGE_NAME, ignore=shutil.ignore_patterns("__pycache__"))
    return STAGE_DIR


def main() -> int:
    """Check preloads, stage the game, then hand the staging directory to pygbag.

    Any arguments are passed through to pygbag, so `--build` builds without serving.
    """
    check_preloads()
    stage_game()
    return subprocess.call([sys.executable, "-m", "pygbag", *sys.argv[1:], str(STAGE_DIR / "main.py")])


if __name__ == "__main__":
    raise SystemExit(main())
