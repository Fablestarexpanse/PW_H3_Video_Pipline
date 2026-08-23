"""refqc.py — measure a reference image before it is allowed to teach a clip (G4; LAWS §8).

  python tools/refqc.py <image> --kind sheet|crop|plate [--figures N] [--block LO HI] [--record <slug>]
  python tools/refqc.py --selftest

Measures: mean luminance (0-255) · median · % pixels > 235 · % pixels < 20 · figure count by
column gap scan (content columns separated by backdrop-coloured gaps) · size.
KNOWN FAILURE of the figure count: views that overlap horizontally (loose hair spanning the gap
on a 768-wide portrait sheet — Wren 811003) read as ONE run. Counted 3/3 on every landscape
1344-wide sheet measured (Lan, Mira, Kaito, Hina) and on Wren 810003. When it reads 1 on a sheet
that plainly shows three views, omit --figures and count by eye; do not lower the threshold.
Refuses (exit 1) when: % > 235 >= 1.5 for crops and plates (LAWS §8: a 26 % near-white macro
cut clips to a white void; a turnaround SHEET is on white by design, so --kind sheet waives
this and relies on --figures) · --figures given and the count differs · --block given and the mean is outside
[LO, HI] (a work-lit plate at 89 against a film at 40-60 came back at 89).
--record <slug> writes the measurements into productions/<slug>/refs/manifest.json for that
file (status stays whatever Ronan set; refqc never approves).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WHITE_LIMIT = 1.5   # percent of pixels > 235


def luma(img: Image.Image) -> np.ndarray:
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def figure_count(img: Image.Image) -> tuple[int, list[tuple[int, int]]]:
    """Count vertical content runs against the backdrop colour sampled from the border."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w, _ = a.shape
    border = np.concatenate([a[:2].reshape(-1, 3), a[-2:].reshape(-1, 3), a[:, :2].reshape(-1, 3), a[:, -2:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    diff = np.abs(a - bg).sum(axis=2) > 60          # pixel is "content"
    band = diff[int(h * 0.15): int(h * 0.85)]         # middle 70 %: skips painted floors, shadows, debris
    col = band.mean(axis=0)                           # fraction of content per column
    content = col > 0.05       # a soft backdrop vignette reads ~0.04 'content' in the gaps (Wren 810003)
    runs, start = [], None
    for x, c in enumerate(content):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append((start, x)); start = None
    if start is not None:
        runs.append((start, w))
    min_w = max(4, w // 40)                            # ignore specks narrower than 2.5 % of width
    runs = [r for r in runs if r[1] - r[0] >= min_w]
    return len(runs), runs


def measure(p: Path) -> dict:
    img = Image.open(p)
    L = luma(img)
    n = L.size
    count, runs = figure_count(img)
    return {
        "file": p.name, "width": img.width, "height": img.height,
        "mean": round(float(L.mean()), 2), "median": round(float(np.median(L)), 2),
        "pct_over_235": round(float((L > 235).sum() * 100 / n), 3),
        "pct_under_20": round(float((L < 20).sum() * 100 / n), 3),
        "figures": count, "figure_runs": runs,
    }


def verdict(m: dict, figures: int | None, block: tuple[float, float] | None, kind: str = "crop") -> list[str]:
    """kind: sheet (white-backdrop turnaround — white limit waived, figures must match) |
             crop (face/grill tight crop — white limit applies) | plate (location — white + block apply)."""
    faults = []
    if kind != "sheet" and m["pct_over_235"] >= WHITE_LIMIT:
        faults.append(f"{m['pct_over_235']} % of pixels > 235 (limit {WHITE_LIMIT}) — crop tighter or re-render; this teaches a white void")
    if kind != "plate" and figures is not None and m["figures"] != figures:   # gap scan is meaningless on a textured plate
        faults.append(f"figure count {m['figures']} != requested {figures} (runs {m['figure_runs']})")
    if block and not (block[0] <= m["mean"] <= block[1]):
        faults.append(f"mean luminance {m['mean']} outside the block it feeds [{block[0]}, {block[1]}]")
    return faults


def record(slug: str, m: dict) -> None:
    import skeleton
    mf = skeleton.PRODUCTIONS / slug / "refs" / "manifest.json"
    data = json.loads(mf.read_text(encoding="utf-8"))
    for r in data.setdefault("refs", []):
        if r.get("file") == m["file"]:
            r["refqc"] = {k: v for k, v in m.items() if k not in ("file", "figure_runs")}
            break
    else:
        data["refs"].append({"file": m["file"], "status": "candidate", "refqc": {k: v for k, v in m.items() if k not in ("file", "figure_runs")}})
    mf.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"recorded  {m['file']} -> {mf.relative_to(skeleton.REPO)}")


def synth(kind: str) -> Image.Image:
    rng = np.random.default_rng(7)
    if kind == "sheet3":        # three dark figures on a light-grey (not white) backdrop
        a = np.full((768, 1344, 3), 225, np.uint8)
        for cx in (260, 672, 1084):
            a[120:700, cx - 90:cx + 90] = (60, 50, 45)
        return Image.fromarray(a)
    if kind == "sheet3_white":  # a real turnaround: pure white backdrop, painted floor strip
        a = np.full((768, 1344, 3), 252, np.uint8)
        for cx in (260, 672, 1084):
            a[120:700, cx - 90:cx + 90] = (60, 50, 45)
        a[700:740] = (200, 190, 170)
        return Image.fromarray(a)
    if kind == "sheet6":        # six figures — the 3264-wide failure
        a = np.full((768, 1344, 3), 225, np.uint8)
        for cx in range(110, 1344, 224):
            a[120:700, cx - 60:cx + 60] = (60, 50, 45)
        return Image.fromarray(a)
    if kind == "white_macro":   # the grill macro: 26 % near-white
        a = (rng.random((768, 1344, 3)) * 120 + 40).astype(np.uint8)
        a[:200] = 250
        return Image.fromarray(a)
    if kind == "plate_dark":    # a correctly dark location plate, mean ~50
        a = (rng.random((768, 1344, 3)) * 40 + 30).astype(np.uint8)
        return Image.fromarray(a)
    if kind == "plate_bright":  # a work-lit plate, mean ~89
        a = (rng.random((768, 1344, 3)) * 40 + 70).astype(np.uint8)
        return Image.fromarray(a)
    raise ValueError(kind)


def selftest() -> int:
    cases = [
        ("sheet3", "sheet", 3, None, False), ("sheet6", "sheet", 3, None, True), ("white_macro", "crop", None, None, True),
        ("plate_dark", "plate", None, (40, 60), False), ("plate_bright", "plate", None, (40, 60), True),
        ("sheet3_white", "sheet", 3, None, False), ("sheet3_white", "crop", None, None, True),
    ]
    fails = 0
    for kind, k, figs, block, expect_refuse in cases:
        img = synth(kind)
        tmp = Path(__file__).resolve().parent.parent / "calibration" / f"_refqc_{kind}.png"
        img.save(tmp)
        m = measure(tmp)
        tmp.unlink()
        faults = verdict(m, figs, block, k)
        ok = bool(faults) == expect_refuse
        fails += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'}      {kind:13} {k:5} mean {m['mean']:6.1f}  >235 {m['pct_over_235']:6.2f} %  figures {m['figures']}  "
              f"-> {'refused' if faults else 'passes'}{'' if ok else ' (expected ' + ('refuse' if expect_refuse else 'pass') + ')'}")
    print(f"\n{'REFUSE: ' + str(fails) + ' selftest failure(s)' if fails else 'selftest passes: 7 synthetic cases separate'}")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("image", nargs="?")
    ap.add_argument("--figures", type=int)
    ap.add_argument("--block", type=float, nargs=2)
    ap.add_argument("--record")
    ap.add_argument("--kind", choices=("sheet", "crop", "plate"), default="crop")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.image:
        print(__doc__)
        return 1
    p = Path(a.image)
    if not p.is_file():
        print(f"REFUSE: {p} not found")
        return 1
    m = measure(p)
    print(f"measured  {m['file']}: {m['width']}x{m['height']}  mean {m['mean']}  median {m['median']}  "
          f">235 {m['pct_over_235']} %  <20 {m['pct_under_20']} %  figures {m['figures']} {m['figure_runs']}")
    faults = verdict(m, a.figures, tuple(a.block) if a.block else None, a.kind)
    for f in faults:
        print(f"REFUSE    {f}")
    if a.record:
        record(a.record, m)
    print("\nREFUSE: refqc" if faults else "\nrefqc passes")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
