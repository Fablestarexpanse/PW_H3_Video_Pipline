"""clipqc.py — numeric QC on every clip, after landing and before the cut (spec §3).

  python tools/clipqc.py <clip.mp4> [--ref plate.png] [--frames N] [--one-shot] [--grid 311,311,362] [--json]
  python tools/clipqc.py --selftest           calibration/manifest.json must separate good from bad

Everything is computed from a 64x36 grayscale decimation of EVERY frame (cheap enough to
sweep a whole cut). Metrics rank suspicion; the filmstrip decides (founding rule 7).

  frames     exact count (the widget lies) — refuses when --frames N differs
  ref_leak   max correlation of the first 4 s against --ref; refuses > 0.50 (measured +0.97 on the
             fault, +0.03 after the fix)
  blown      mean luminance > 150 on any frame — refuses (one-frame white pops on hard cuts)
  black      mean luminance < 8 on any frame — refuses
  cuts       |frame-to-frame luminance diff| > 20, adjacent (strobe) pairs and --grid slot
             boundaries ignored; refuses on a --one-shot clip
  local      block stats on an 8x6 grid per frame: peak/median block motion, largest single-
             frame jump / median motion, edge-energy growth (last s / first s). ADVISORY — no
             calibrated known-bad case yet, so it ranks suspicion and never refuses.
  grade      mean luminance, for keeping a block consistent (advisory)

Calibration rule (spec §3): --selftest must separate calibration/bad/* from calibration/good/*
on every refusing metric it uses. If a metric cannot, it is removed, not tuned.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402

W, H = 64, 36
FPS = 24
THRESH = {"ref_leak": 0.50, "blown": 150.0, "black": 8.0, "cut": 20.0,
          "peak_over_median": 25.0, "jump_over_median": 40.0, "edge_growth": 2.5}
MANIFEST = paths.REPO / "calibration" / "manifest.json"


def decimate(p: Path) -> np.ndarray | None:
    # -fps_mode passthrough: measure the frames that exist, not a CFR resample (which duplicated
    # a frame across a concat boundary with an edit-list offset — measured 2026-08-23).
    out = subprocess.run([str(paths.FFMPEG), "-v", "error", "-i", str(p), "-fps_mode", "passthrough",
                          "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    if not out:
        return None
    return np.frombuffer(out, dtype=np.uint8).reshape(-1, H, W).astype(np.float32)


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def local_stats(A: np.ndarray) -> dict:
    """8x6 block grid; motion = mean |diff| per block per frame."""
    n = len(A)
    if n < 3:
        return {"peak_over_median": 0.0, "jump_over_median": 0.0, "edge_growth": 1.0}
    d = np.abs(np.diff(A, axis=0))                                   # (n-1, H, W)
    blocks = d.reshape(n - 1, 6, H // 6, 8, W // 8).mean(axis=(2, 4))  # (n-1, 6, 8)
    med = float(np.median(blocks)) + 1e-3
    peak = float(blocks.max())
    per_frame_peak = blocks.reshape(n - 1, -1).max(axis=1)
    jump = float(np.max(np.abs(np.diff(per_frame_peak)))) if n > 3 else 0.0
    gy, gx = np.gradient(A, axis=(1, 2))
    edge = np.sqrt(gx * gx + gy * gy).reshape(n, -1).mean(axis=1)
    head, tail = edge[:FPS].mean() + 1e-3, edge[-FPS:].mean() + 1e-3
    return {"peak_over_median": round(peak / med, 2), "jump_over_median": round(jump / med, 2),
            "edge_growth": round(float(max(tail / head, head / tail)), 2)}


def measure(p: Path, ref: Path | None, grid: list[int] | None) -> dict:
    A = decimate(p)
    if A is None:
        return {"file": p.name, "unreadable": True}
    n = len(A)
    lum = A.reshape(n, -1).mean(1)
    m = {"file": p.name, "frames": n, "seconds": round(n / FPS, 3), "grade": round(float(lum.mean()), 1),
         "lum_min": round(float(lum.min()), 1), "lum_max": round(float(lum.max()), 1),
         "blown": [int(i) for i in np.where(lum > THRESH["blown"])[0][:12]],
         "black": [int(i) for i in np.where(lum < THRESH["black"])[0][:12]]}
    if ref is not None:
        R = np.asarray(Image.open(ref).convert("L").resize((W, H)), dtype=np.float32)
        c = [corr(A[f], R) for f in range(min(4 * FPS, n))]
        m["ref_leak"] = round(max(c), 3)
        m["ref_leak_frame"] = int(np.argmax(c))
    cuts = list(np.where(np.abs(np.diff(lum)) > THRESH["cut"])[0] + 1)
    strobe = {c for c in cuts if (c + 1) in cuts or (c - 1) in cuts}
    real = [int(c) for c in cuts if c not in strobe]
    if grid:
        acc, bounds = 0, set()
        for L in grid:
            acc += L; bounds.add(acc)
        real = [c for c in real if not any(abs(c - b) < 3 for b in bounds)]
    m["cuts"] = real[:12]
    m["strobe_frames"] = len(strobe)
    m.update(local_stats(A))
    return m


def verdict(m: dict, frames: int | None, one_shot: bool) -> list[str]:
    if m.get("unreadable"):
        return ["unreadable"]
    f = []
    if frames is not None and m["frames"] != frames:
        f.append(f"frames {m['frames']} != expected {frames}")
    if "ref_leak" in m and m["ref_leak"] > THRESH["ref_leak"]:
        f.append(f"ref_leak {m['ref_leak']:+.3f} at frame {m['ref_leak_frame']} > {THRESH['ref_leak']} — the plate is being reproduced as picture")
    if m["blown"]:
        f.append(f"blown frames {m['blown']} (luminance > {THRESH['blown']})")
    if m["black"]:
        f.append(f"black frames {m['black']} (luminance < {THRESH['black']})")
    if one_shot and m["cuts"]:
        f.append(f"cuts at {m['cuts']} on a one-shot clip")
    # Local block stats are ADVISORY until calibration/ holds a known-bad "local" case: on the
    # WTTB board (2026-08-23) peak/median > 25 flagged shipped clips as often as re-rolls, so
    # by the calibration rule it cannot refuse. Reported in the measured line; ranks suspicion.
    return f


def report(m: dict, faults: list[str]) -> None:
    if m.get("unreadable"):
        print(f"REFUSE    {m['file']}: unreadable"); return
    print(f"measured  {m['file']}: {m['frames']} f ({m['seconds']} s)  grade {m['grade']} [{m['lum_min']}-{m['lum_max']}]"
          + (f"  ref_leak {m['ref_leak']:+.3f}@{m['ref_leak_frame']}" if "ref_leak" in m else "")
          + f"  cuts {m['cuts'] or 'none'} ({m['strobe_frames']} strobe)  local p/m {m['peak_over_median']} j/m {m['jump_over_median']} edge {m['edge_growth']}")
    for x in faults:
        print(f"REFUSE    {m['file']}: {x}")


def selftest() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    good, bad = man.get("good", []), man.get("bad", [])
    if not good or not bad:
        print(f"REFUSE: calibration/manifest.json needs good[] and bad[] entries (media under {paths.MEDIA / 'calibration'})")
        return 1
    fails = 0
    for label, items, expect in (("good", good, False), ("bad", bad, True)):
        for it in items:
            p = paths.MEDIA / "calibration" / label / it["file"]
            ref = paths.MEDIA / "calibration" / it["ref"] if it.get("ref") else None
            if not p.is_file():
                print(f"FAIL      {label}/{it['file']} missing on the drive"); fails += 1; continue
            m = measure(p, ref, None)
            faults = verdict(m, it.get("frames"), it.get("one_shot", False))
            codes = [x.split()[0] for x in faults]
            if expect:
                ok = it["fault"] in codes
                print(f"{'ok  ' if ok else 'FAIL'}      bad/{it['file']}: expected [{it['fault']}], got {codes}")
            else:
                ok = not faults
                print(f"{'ok  ' if ok else 'FAIL'}      good/{it['file']}: {codes or 'passes'}")
            fails += 0 if ok else 1
    print(f"\n{'REFUSE: ' + str(fails) + ' selftest failure(s) — remove the metric, do not tune it' if fails else f'selftest passes: {len(good)} good, {len(bad)} bad separate'}")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--ref"); ap.add_argument("--frames", type=int); ap.add_argument("--one-shot", action="store_true")
    ap.add_argument("--grid"); ap.add_argument("--json", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.clips:
        print(__doc__); return 1
    grid = [int(x) for x in a.grid.split(",")] if a.grid else None
    rc = 0
    for c in a.clips:
        m = measure(Path(c), Path(a.ref) if a.ref else None, grid)
        faults = verdict(m, a.frames, a.one_shot)
        if a.json:
            print(json.dumps({**m, "faults": faults}, ensure_ascii=False))
        else:
            report(m, faults)
        rc |= 1 if faults else 0
    print("\nREFUSE: clipqc" if rc else "\nclipqc passes")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
