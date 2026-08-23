"""paths.py — resolve every host path the pipeline depends on.

The ONLY file in the repo that knows a drive letter. Everything else imports
from here. Run directly to print what resolves and what is missing; exits 1
if anything required is absent. Creates the F:\\MovieMaker skeleton (spec §5b)
when MOVIEMAKER_MEDIA does not exist.

Env vars (all optional, defaults are for Ronan's box):
  MOVIEMAKER_FFMPEG   MOVIEMAKER_FFPROBE   MOVIEMAKER_COMFY   MOVIEMAKER_MEDIA
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Windows consoles default to cp1252; workflow names contain em-dashes and macrons.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

_DEFAULTS = {
    "MOVIEMAKER_COMFY": r"F:\Stability Matrix\Packages\ComfyUI",
    "MOVIEMAKER_MEDIA": r"F:\MovieMaker",
}

MEDIA_SKELETON = ("calibration/good", "calibration/bad")


def _exe(env: str, name: str) -> Path | None:
    v = os.environ.get(env)
    if v:
        return Path(v) if Path(v).is_file() else None
    found = shutil.which(name)
    return Path(found) if found else None


def _dir(env: str) -> Path:
    return Path(os.environ.get(env) or _DEFAULTS[env])


FFMPEG = _exe("MOVIEMAKER_FFMPEG", "ffmpeg")
FFPROBE = _exe("MOVIEMAKER_FFPROBE", "ffprobe")
COMFY_ROOT = _dir("MOVIEMAKER_COMFY")
COMFY_INPUT = COMFY_ROOT / "input"
COMFY_OUTPUT = COMFY_ROOT / "output"
COMFY_WORKFLOWS = COMFY_ROOT / "user" / "default" / "workflows"
MEDIA = _dir("MOVIEMAKER_MEDIA")

# (label, value, required, kind)
RESOLVED = [
    ("repo", REPO, True, "dir"),
    ("ffmpeg", FFMPEG, True, "file"),
    ("ffprobe", FFPROBE, True, "file"),
    ("comfy_root", COMFY_ROOT, True, "dir"),
    ("comfy_input", COMFY_INPUT, True, "dir"),
    ("comfy_output", COMFY_OUTPUT, True, "dir"),
    ("comfy_workflows", COMFY_WORKFLOWS, True, "dir"),
    ("media", MEDIA, True, "dir"),
    ("python", Path(sys.executable), True, "file"),
]


def ensure_media_skeleton() -> list[Path]:
    """Create MEDIA and its §5b skeleton. Returns the dirs that were created."""
    created = []
    for rel in ("",) + MEDIA_SKELETON:
        p = MEDIA / rel
        if not p.exists():
            p.mkdir(parents=True)
            created.append(p)
    return created


def media_for(production: str, *parts: str) -> Path:
    """F:\\MovieMaker\\<slug>\\... mirrors productions/<slug>/... exactly."""
    return MEDIA.joinpath(production, *parts)


def check() -> int:
    created = ensure_media_skeleton()
    for p in created:
        print(f"created   {p}")
    missing = []
    for label, value, required, kind in RESOLVED:
        ok = value is not None and (value.is_file() if kind == "file" else value.is_dir())
        print(f"{'ok     ' if ok else 'MISSING'}  {label:16} {value if value else '(not found)'}")
        if required and not ok:
            missing.append(label)
    if sys.version_info < (3, 10):
        print(f"MISSING  python>=3.10     have {sys.version.split()[0]}")
        missing.append("python>=3.10")
    if missing:
        print(f"\nREFUSE: {len(missing)} required path(s) missing: {', '.join(missing)}")
        return 1
    print(f"\nall {len(RESOLVED)} paths resolve")
    return 0


if __name__ == "__main__":
    sys.exit(check())
