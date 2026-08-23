"""new_production.py — the only way a production folder comes to exist (spec §5c).

  python tools/new_production.py <slug> --format film|show --title "<Title>" [--unit "S01E01 - Name"]

Copies templates/production/, writes template_version, stamps TITLE/FORMAT into
identity.py, creates the media mirror on the drive, then runs residue.py and
drift.py on the result. Refuses if the slug exists, is not [a-z0-9_], or the
template is missing anything.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402
import skeleton  # noqa: E402

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def copy_unit(dst: Path) -> None:
    src = skeleton.TEMPLATE_DIR / "_unit"
    for rel in skeleton.UNIT_REQUIRED:
        dst.joinpath(rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / rel, dst / rel)
    (dst / "prompts").mkdir(exist_ok=True)
    shutil.copyfile(src / "prompts" / ".gitkeep", dst / "prompts" / ".gitkeep")


def create(slug: str, fmt: str, title: str, unit: str | None) -> int:
    if not SLUG_RE.match(slug):
        print(f"REFUSE: slug {slug!r} must match {SLUG_RE.pattern}")
        return 1
    if fmt not in ("film", "show"):
        print(f"REFUSE: format must be film or show, got {fmt!r}")
        return 1
    if fmt == "show" and not (unit and skeleton.UNIT_RE.match(unit)):
        print("REFUSE: a show needs --unit 'S01E01 - <name>'")
        return 1
    if not title.strip():
        print("REFUSE: --title is blank")
        return 1
    dst = skeleton.PRODUCTIONS / slug
    if dst.exists():
        print(f"REFUSE: {dst} already exists")
        return 1
    for rel in skeleton.ROOT_REQUIRED:
        if rel != "template_version" and not (skeleton.TEMPLATE_DIR / rel).is_file():
            print(f"REFUSE: template is missing {rel}")
            return 1

    dst.mkdir(parents=True)
    for rel in skeleton.ROOT_REQUIRED:
        if rel == "template_version":
            continue
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(skeleton.TEMPLATE_DIR / rel, dst / rel)
    (dst / "template_version").write_text(f"{skeleton.template_version()}\n", encoding="utf-8")

    ident = (dst / "identity.py").read_text(encoding="utf-8")
    ident = ident.replace('TITLE = ""', f"TITLE = {title!r}", 1).replace('FORMAT = ""', f"FORMAT = {fmt!r}", 1)
    (dst / "identity.py").write_text(ident, encoding="utf-8")

    unit_dir = dst if fmt == "film" else dst / unit
    copy_unit(unit_dir)

    media = paths.media_for(slug)
    for rel in ("refs/candidates",):
        (media / rel).mkdir(parents=True, exist_ok=True)
    mu = media if fmt == "film" else media / unit
    for rel in ("clips", "filmstrips", "cuts"):
        (mu / rel).mkdir(parents=True, exist_ok=True)

    print(f"created   productions/{slug}  (format={fmt}, template_version={skeleton.template_version()})")
    print(f"created   {media}  (media mirror)")

    import residue, drift  # noqa: E402
    rc = residue.check(dst)
    if rc:
        return rc
    return drift.check_production(dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--format", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--unit")
    a = ap.parse_args()
    sys.exit(create(a.slug, a.format, a.title, a.unit))
