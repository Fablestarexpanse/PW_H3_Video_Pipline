"""skeleton.py — the one definition of what a production folder may contain.

Read by new_production.py (creates), drift.py (refuses), migrate.py (repairs).
Nothing else knows the layout.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from paths import REPO

TEMPLATE_DIR = REPO / "templates" / "production"
TEMPLATE_VERSION_FILE = REPO / "templates" / "TEMPLATE_VERSION"
PRODUCTIONS = REPO / "productions"

UNIT_RE = re.compile(r"^S\d{2}E\d{2} - .+$")           # show units
CHAR_RE = re.compile(r"^[a-z0-9_]+\.md$|^_TEMPLATE\.md$")
APPROVED_RE = re.compile(r"^[A-Za-z0-9_]+_APPROVED_\d+\.png$")
LINES_RE = re.compile(r"^[a-z0-9_]+\.lines$")

# Files every production must have at its root (relative), copied from TEMPLATE_DIR.
ROOT_REQUIRED = (
    "identity.py", "template_version", "brief.md", "development.md",
    "refs/manifest.json", "renders.jsonl",
    "characters/_TEMPLATE.md", "locations/_TEMPLATE.md",
)
# Files every unit must have (relative to the unit folder).
UNIT_REQUIRED = ("beats.csv", "slot_names.txt", "jobs.jsonl", "postmortem.md")

# Fields identity.py must declare — and the only ones it may.
IDENTITY_FIELDS = ("TITLE", "FORMAT", "ASPECT", "WORLD", "STYLE_STACK", "CAST",
                   "LOCATIONS", "VOICES", "AUDIO", "WORKFLOWS")


def template_version() -> int:
    return int(TEMPLATE_VERSION_FILE.read_text(encoding="utf-8").strip())


def productions() -> list[Path]:
    if not PRODUCTIONS.is_dir():
        return []
    return sorted(p for p in PRODUCTIONS.iterdir() if p.is_dir() and (p / "identity.py").is_file())


def load_identity(prod: Path):
    """Import <prod>/identity.py as a module without touching sys.modules."""
    spec = importlib.util.spec_from_file_location(f"identity_{prod.name}", prod / "identity.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def units(prod: Path, fmt: str) -> list[Path]:
    """film: the production folder itself. show: every 'S01E01 - <name>' folder."""
    if fmt == "film":
        return [prod]
    return sorted(p for p in prod.iterdir() if p.is_dir() and UNIT_RE.match(p.name))


def _allowed_unit_file(rel: Path) -> bool:
    parts = rel.parts
    if len(parts) == 1:
        return parts[0] in UNIT_REQUIRED
    if parts[0] == "prompts" and len(parts) == 2:
        return parts[1] == ".gitkeep" or bool(LINES_RE.match(parts[1]))
    return False


def allowed(prod: Path, fmt: str, rel: Path) -> bool:
    """Is this file (relative to the production root) permitted by the skeleton?"""
    parts = rel.parts
    if len(parts) == 1:
        return parts[0] in ROOT_REQUIRED or (fmt == "film" and _allowed_unit_file(rel))
    head = parts[0]
    if head == "characters" or head == "locations":
        return len(parts) == 2 and bool(CHAR_RE.match(parts[1]))
    if head == "refs":
        return len(parts) == 2 and (parts[1] == "manifest.json" or bool(APPROVED_RE.match(parts[1])))
    if head == "__pycache__":
        return True  # gitignored; never committed
    if fmt == "film" and head == "prompts":
        return _allowed_unit_file(rel)
    if fmt == "show" and UNIT_RE.match(head):
        return _allowed_unit_file(Path(*parts[1:]))
    return False


def walk(prod: Path):
    for p in prod.rglob("*"):
        if p.is_file():
            yield p.relative_to(prod)


if __name__ == "__main__":
    print(f"template version {template_version()}")
    for p in productions():
        print(f"production {p.name}")
    sys.exit(0)
