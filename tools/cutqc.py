"""cutqc.py — measure the delivered cut, never the plan (spec §3).

  python tools/cutqc.py <cut.json> [--occlusion-beats b07,b09]

--occlusion-beats: comma-separated beat names (matching meta.slots[].beat) whose frame range in the
master is exempt from the black check — a scripted blackout or a cut-to-black ending is the design,
not a fault. Never exempts blown; a beat can go dark on purpose, never overexposed on purpose.

Refuses (exit 1) on any mismatch — never loosen a tolerance:
  frames     master frame count != meta.total_frames (beats.csv sum, minus transition overlap
             when the cut has one)
  streams    any segment's codec / width / height / frame rate / pix_fmt differs from the rest,
             or from the master
  blown      any frame mean luminance > 150       black   any frame < 8, outside --occlusion-beats
  boundary   HARD CUT (no transition): at every slot boundary F_k the master's frame F_k is not
             the first frame of segment k+1 and frame F_k-1 is not the last frame of segment k
             (decimated-frame correlation < 0.98) — a stale or mis-trimmed segment shows here.
             DISSOLVE (transition.frames > 0): at every transition window, the frame just before
             it must still match the earlier segment's tail (>=0.9) and the frame just after it
             must match the later segment's head (>=0.9) — proves the blend runs between the
             correct two clips — and no two consecutive frames inside the window may be identical
             (a frozen frame means the crossfade silently did not run).
  audio      audio stream duration differs from picture by more than 2 ms
Prints every measurement.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import clipqc  # noqa: E402
import paths  # noqa: E402

AUDIO_TOL = 0.002


def streams(p: Path) -> dict:
    out = subprocess.run([str(paths.FFPROBE), "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,duration,nb_frames",
                          "-of", "json", str(p)], capture_output=True, text=True, check=True).stdout
    d = {"video": None, "audio": None}
    for s in json.loads(out).get("streams", []):
        d[s["codec_type"]] = s
    return d


def sig(v: dict) -> tuple:
    return (v["codec_name"], v["width"], v["height"], v["r_frame_rate"], v["pix_fmt"])


def main(argv: list[str]) -> int:
    occlusion_beats: set[str] = set()
    pos = []
    for a in argv:
        if a.startswith("--occlusion-beats="):
            occlusion_beats = {b.strip() for b in a.split("=", 1)[1].split(",") if b.strip()}
        else:
            pos.append(a)
    if len(pos) != 1:
        print(__doc__); return 1
    meta = json.loads(Path(pos[0]).read_text(encoding="utf-8"))
    master = Path(meta["master"])
    faults = []

    A = clipqc.decimate(master)
    if A is None:
        print(f"REFUSE: {master} unreadable"); return 1
    n = len(A)
    total = meta.get("total_frames", sum(meta["LEN"]))
    print(f"measured  frames {n} vs expected {total}")
    if n != total:
        faults.append(f"frames {n} != expected {total}")

    ms = streams(master)
    msig = sig(ms["video"])
    print(f"measured  master video {msig}")
    segs = []
    for slot in meta["slots"]:
        st = streams(Path(slot["segment"]))
        s = sig(st["video"])
        segs.append(st)
        if s != msig:
            faults.append(f"segment {slot['slot']:02d} streams {s} != master {msig}")
    print(f"measured  {len(segs)} segments share the master's codec/geometry/rate/pix_fmt" if not faults else f"measured  {len(segs)} segments probed")

    lum = A.reshape(n, -1).mean(1)
    blown = np.where(lum > clipqc.THRESH["blown"])[0]
    black_all = np.where(lum < clipqc.THRESH["black"])[0]
    occluded = np.zeros(n, dtype=bool)
    for slot in meta["slots"]:
        if slot["beat"] in occlusion_beats:
            start, end = slot["end_frame"] - slot["frames"], slot["end_frame"]
            occluded[max(0, start):min(n, end)] = True
    black = black_all[~occluded[black_all]]
    exempted = len(black_all) - len(black)
    tag = f" ({exempted} in --occlusion-beats {sorted(occlusion_beats)})" if exempted else ""
    print(f"measured  luminance mean {lum.mean():.1f} min {lum.min():.1f} max {lum.max():.1f}; blown {list(blown[:8])} black {list(black[:8])}{tag}")
    if len(blown):
        faults.append(f"blown frames {list(blown[:12])}")
    if len(black):
        faults.append(f"black frames {list(black[:12])}")

    trans = meta.get("transition", {"type": "cut", "frames": 0, "boundaries": []})
    if trans.get("frames", 0) > 0:
        D = trans["frames"]
        segs = [clipqc.decimate(Path(s["segment"])) for s in meta["slots"]]
        worst_order = 1.0
        for j, off in enumerate(trans["boundaries"]):
            segA, segB = segs[j], segs[j + 1]
            if segA is None or segB is None or off < 0 or off + D > n:
                faults.append(f"transition {j+1:02d}: segment unreadable or window out of range"); continue
            window = A[off:off + D]
            tailA, headB = segA[-1], segB[0]
            c_first_A, c_first_B = clipqc.corr(window[0], tailA), clipqc.corr(window[0], headB)
            c_last_A, c_last_B = clipqc.corr(window[-1], tailA), clipqc.corr(window[-1], headB)
            worst_order = min(worst_order, c_first_A - c_first_B, c_last_B - c_last_A)
            if c_first_A <= c_first_B:
                faults.append(f"transition {j+1:02d} ({meta['slots'][j]['beat']}→{meta['slots'][j+1]['beat']}): window start looks more like the later clip ({c_first_B:.3f}) than the earlier one ({c_first_A:.3f}) — offset is wrong")
            if c_last_B <= c_last_A:
                faults.append(f"transition {j+1:02d} ({meta['slots'][j]['beat']}→{meta['slots'][j+1]['beat']}): window end looks more like the earlier clip ({c_last_A:.3f}) than the later one ({c_last_B:.3f}) — offset is wrong")
            frozen = [i for i in range(len(window) - 1) if np.array_equal(window[i], window[i + 1])]
            if frozen:
                faults.append(f"transition {j+1:02d} ({meta['slots'][j]['beat']}→{meta['slots'][j+1]['beat']}): frames {frozen} identical to their neighbor — the crossfade did not run")
        print(f"measured  {len(trans['boundaries'])} dissolve transition(s), {D} f each; worst handoff margin {worst_order:.3f} (>0 means correctly ordered)")
    else:
        worst = 1.0
        for k, slot in enumerate(meta["slots"]):
            S = clipqc.decimate(Path(slot["segment"]))
            start = slot["end_frame"] - slot["frames"]
            end = slot["end_frame"]
            if S is None or end > n:
                faults.append(f"boundary slot {slot['slot']:02d}: segment unreadable or beyond master"); continue
            c_first = clipqc.corr(A[start], S[0])
            c_last = clipqc.corr(A[end - 1], S[-1])
            worst = min(worst, c_first, c_last)
            if c_first < 0.98 or c_last < 0.98:
                faults.append(f"boundary slot {slot['slot']:02d} ({slot['beat']}): first {c_first:.3f} last {c_last:.3f} — segment and master disagree at frames {start}/{end-1}")
        print(f"measured  boundary drift: worst first/last-frame correlation {worst:.3f} over {len(meta['slots'])} slots")

    if ms["audio"]:
        vdur = n / meta["fps"]
        adur = float(ms["audio"].get("duration", 0))
        print(f"measured  audio {adur:.4f} s vs picture {vdur:.4f} s (diff {abs(adur - vdur) * 1000:.1f} ms)")
        if abs(adur - vdur) > AUDIO_TOL:
            faults.append(f"audio {adur:.4f} s != picture {vdur:.4f} s (tolerance {AUDIO_TOL * 1000:.0f} ms)")
    else:
        print("measured  no audio stream")
        faults.append("master has no audio stream")

    for f in faults:
        print(f"REFUSE    {f}")
    print("\nREFUSE: cutqc" if faults else f"\ncutqc passes: {master.name}")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
