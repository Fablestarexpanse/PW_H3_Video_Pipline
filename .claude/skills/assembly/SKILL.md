---
name: assembly
description: Assemble landed clips into a cut, verify it, and produce the review copies (CUT stage). Use when running assemble.py, cutqc.py, tag.py, choosing takes, or delivering a cut.
---

# Assembly — the CUT stage

Every cut ships as **three files**: `cutNN.mp4` (the clean master — nothing is ever burned into it),
`cutNN_TAGGED.mp4` (review copy: `SLOT NN <beat name>` top right, `+Ns` within the slot under it,
running timecode bottom left) and `cutNN_web.mp4` (720 wide, crf 30 — the 30 MB delivery cap).
Notes then come back as *"slot 17, +4s"*, which maps straight onto a prompt line's slot-relative
timestamps.

## The commands

```
python tools/assemble.py <slug> <unit|.> cutNN [--head 24] [--dry-run]
python tools/cutqc.py  F:/MovieMaker/<slug>/<unit>/cuts/cutNN.json
python tools/tag.py    F:/MovieMaker/<slug>/<unit>/cuts/cutNN.json
```

`assemble.py --dry-run` prints the **SRC table** — one line per slot naming the exact clip file, its
job id and the beat name — before anything is built. Read it. After a board with twelve re-rolls,
`seg_14` could have come from any of four takes; two stale segments once survived a rebuild because
nobody re-made them. v2 rebuilds every segment from the table every time (~20 s for three slots).

## How a source is chosen

The take for a beat is the `jobs.jsonl` row with id `<beat>_s<seed>` and `status: landed`. When
several landed, set `"pick": true` on exactly one; assemble refuses otherwise. A rejected file is
renamed `__rej_<reason>` on the drive and is never picked.

## How the cut is built (measured, not proposed)

- Boundaries in **frames** (`beats.csv`), never seconds. Each segment: `trim=start_frame=HEAD:
  end_frame=HEAD+frames`, `setpts` reset, libx264 veryfast crf 16, yuv420p, 24 fps. `--head` skips
  the clip's head handle (default 24 f ≈ 1 s; LAWS: trim handles ~1.0 s head / ≥0.8 s tail).
- Segments are **video only**, stream-copied into the picture. Audio in a segment gave the concat an
  edit-list offset and a non-monotonic DTS at the first seam — a CFR decode then *duplicated a frame*.
- Audio is muxed **once**: the `identity.AUDIO` master, or the clips' own audio as PCM segments
  concatenated — cut with `atrim` to the exact picture length (reads equal to the sample).
- Hard cuts only. A dissolve is its own short segment spliced into the list, only where wanted.
- A chained `xfade` re-encodes the whole timeline per stage and does not scale — not used.

## What cutqc refuses (never loosen a tolerance)

frame count ≠ the beats sum · any segment's codec/geometry/rate/pix_fmt ≠ the master · a blown (>150)
or black (<8) frame anywhere · **boundary drift**: at every slot boundary the master's first/last frame
must correlate ≥ 0.98 with the segment's (a stale or mis-trimmed segment shows as −0.065) · audio ≠
picture by more than 2 ms. A fault means rebuild, not patch. Fix a one-frame white pop at a clip's tail
by cloning the last clean frame (`tpad=stop_mode=clone`) in a new take, never in the cut.

## Sweep the whole cut, not the clip you just made

`python tools/clipqc.py F:/MovieMaker/<slug>/<unit>/clips/*.mp4 --ref <plate>` on the board, and cutqc on
every delivered file. A one-frame white pop shipped in every previous version of a film before a sweep
found it. Decode with `-fps_mode passthrough` whenever counting frames (clipqc/cutqc do).

## Chain (tnew) assemblies

`mm_chain_v1` assembles its own segments (stream copy + mux of the MUX audio) into
`output/h3_chain/<run_name>/final.mp4`; `landed.py` picks that up. At context 22 / anchor head every
segment after the first delivers `length − 22` frames: `total = 15.083 + (N − 1) × 14.167` s at 362.
