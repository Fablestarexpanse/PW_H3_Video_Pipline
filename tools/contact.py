"""contact.py — every approved reference in a production, on one sheet.

  python tools/contact.py <slug> [--cols N] [--out path.png]

Refs are approved one seed at a time (REFS gate) and reviewed one at a time — nothing puts them
side by side. A wrong corner, a drifted prop, or a character/location pair that reads fine alone
and clashes next to the others is invisible in that order and obvious in one look across the
whole set. This is that look: every `refs/*_APPROVED_*.png` in a production, thumbnailed onto one
grid with its filename underneath, in identity.CAST/LOCATIONS declaration order where a ref is
declared there, then alphabetically for anything else approved but not yet wired into identity.

Writes <media>/<slug>/contact/contact.png (media, never git). Refuses on zero approved refs.

The idea — one grid of every plate instead of one at a time — comes from `contact.py` in Garrett
Bloome's rtome-showrunner-pipeline (github.com/KerbalTheGathering/rtome-showrunner-pipeline), a
sibling ComfyUI production pipeline. This is a from-scratch reimplementation against our own
identity.py/refs layout, not a port of his code.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import paths  # noqa: E402
import skeleton  # noqa: E402

CELL_W, CELL_H = 320, 220
PAD = 12
LABEL_H = 24

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
]


class Refuse(Exception):
    pass


def _font(size: int):
    for f in FONT_CANDIDATES:
        if Path(f).is_file():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def ordered_refs(prod: Path) -> list[tuple[str, Path]]:
    """(label, path) pairs — identity declaration order first, then any other approved file."""
    ident = skeleton.load_identity(prod)
    declared: dict[str, Path] = {}
    for group in ("CAST", "LOCATIONS"):
        for key, row in getattr(ident, group, {}).items():
            p = prod / row["sheet"]
            if p.is_file():
                declared[key] = p
    all_approved = sorted((prod / "refs").glob("*_APPROVED_*.png"))
    seen = set(declared.values())
    extra = [(p.stem.split("_APPROVED_")[0], p) for p in all_approved if p not in seen]
    return list(declared.items()) + extra


def build(prod: Path, cols: int, out: Path) -> int:
    refs = ordered_refs(prod)
    if not refs:
        raise Refuse(f"no approved refs found under {prod / 'refs'}")
    rows = (len(refs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * CELL_W, rows * (CELL_H + LABEL_H)), "white")
    draw = ImageDraw.Draw(sheet)
    font = _font(16)
    for i, (label, path) in enumerate(refs):
        r, c = divmod(i, cols)
        x0, y0 = c * CELL_W, r * (CELL_H + LABEL_H)
        img = Image.open(path).convert("RGB")
        img.thumbnail((CELL_W - PAD * 2, CELL_H - PAD * 2))
        cx = x0 + (CELL_W - img.width) // 2
        cy = y0 + (CELL_H - img.height) // 2
        sheet.paste(img, (cx, cy))
        text = f"{label}  ({path.name})"
        tw = draw.textlength(text, font=font)
        draw.text((x0 + (CELL_W - min(tw, CELL_W - 8)) // 2, y0 + CELL_H + 2), text, fill="black", font=font)
        print(f"  {i+1:02d}  {label:12} {path.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"\ncontact   {len(refs)} ref(s), {cols}x{rows} grid -> {out}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    prod = skeleton.PRODUCTIONS / a.slug
    out = Path(a.out) if a.out else paths.media_for(a.slug, "contact", "contact.png")
    try:
        return build(prod, a.cols, out)
    except Refuse as e:
        print(f"\nREFUSE: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
