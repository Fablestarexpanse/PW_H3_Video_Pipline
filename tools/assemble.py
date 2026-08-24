"""assemble.py — frame-exact segments, stream-copy concat, full rebuild every time (spec §3).

  python tools/assemble.py <slug> <unit|.> <cut_name> [--head 24] [--transition N] [--dry-run]

Source per beat (the named SRC): the one jobs.jsonl row for that beat (id = "<beat>_s<seed>")
with status landed — or, when several landed, the one with "pick": true. Refuses when a beat
has no landed take, has several with no pick, or a picked file is missing / "__rej_".
Every segment is rebuilt from its SRC with trim=start_frame=HEAD:end_frame=HEAD+frames
(frames from beats.csv) and setpts reset, -preset veryfast -crf 16 yuv420p 24 fps, scaled to the
board's canvas (the most common SRC resolution — a board mixing mm_clip_v1 and mm_chain_v1 has two
native output sizes; every segment is scaled to match regardless of source graph).
Segments are VIDEO ONLY (audio in a segment gives the concat an edit-list offset and a
non-monotonic DTS at the first boundary). Audio: the identity.AUDIO master, or the clips' own
audio trimmed per segment to PCM and concatenated; either is muxed once over the stream-copied
picture with atrim to the exact picture length (audio == picture to the sample).

--transition N (frames, default 0 = hard cut): every internal slot boundary becomes an N-frame
crossfade dissolve instead of a stream-copy join. Each transition consumes N frames from the tail
of the earlier segment and N frames from the head of the later one (standard editorial overlap),
so the master is (n_slots-1)*N frames SHORTER than the sum of beats.csv frames — this is by
design, not a fault; cutqc checks against the true post-transition total, not the beats.csv sum.
Requires re-encoding via ffmpeg's xfade/acrossfade filters (no stream-copy path when N>0).

Writes <media>/<unit>/cuts/<cut_name>.mp4 and <cut_name>.json (SRC table, LEN, boundaries,
transition). Never deletes a render; only the cut's own segments are rebuilt.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import landed  # noqa: E402
import paths  # noqa: E402
import render  # noqa: E402
import skeleton  # noqa: E402

FPS = 24


class Refuse(Exception):
    pass


def beats_of(unit: Path) -> list[dict]:
    with (unit / "beats.csv").open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("beat", "").strip()]


def slot_names(unit: Path, n: int) -> list[str]:
    names = [l.strip() for l in (unit / "slot_names.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(names) != n:
        raise Refuse(f"slot_names.txt has {len(names)} names for {n} beats")
    return names


def pick_sources(unit: Path, beats: list[dict]) -> list[dict]:
    rows = render.read_rows(unit / "jobs.jsonl")
    srcs = []
    for b in beats:
        beat = b["beat"].strip()
        cands = [r for r in rows if r.get("id", "").startswith(beat + "_s") and r.get("status") == "landed"]
        if not cands:
            raise Refuse(f"beat {beat}: no landed take in jobs.jsonl")
        picks = [r for r in cands if r.get("pick")]
        if len(cands) > 1 and len(picks) != 1:
            raise Refuse(f"beat {beat}: {len(cands)} landed takes {[r['id'] for r in cands]} and {len(picks)} picked — set \"pick\": true on exactly one")
        row = picks[0] if picks else cands[0]
        files = row.get("landed_files") or []
        vids = [f for f in files if Path(f).suffix.lower() in landed.VIDEO_EXT]
        if len(vids) != 1:
            raise Refuse(f"beat {beat}: take {row['id']} landed {len(vids)} video file(s)")
        srcs.append({"beat": beat, "job": row["id"], "file": vids[0], "frames": int(b["frames"])})
    return srcs


def media_dir(prod: Path, unit: Path, *parts: str) -> Path:
    rel = [] if unit == prod else [unit.name]
    return paths.media_for(prod.name, *rel, *parts)


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise Refuse(f"ffmpeg failed: {' '.join(cmd[:6])}…\n{r.stderr[-800:]}")


def assemble(prod: Path, unit: Path, name: str, head: int, transition: int, dry: bool) -> int:
    ident = skeleton.load_identity(prod)
    beats = beats_of(unit)
    if not beats:
        raise Refuse("beats.csv is empty")
    names = slot_names(unit, len(beats))
    srcs = pick_sources(unit, beats)
    if transition and transition * 2 >= min(s["frames"] for s in srcs):
        raise Refuse(f"--transition {transition} f is not less than half the shortest beat's frames — overlap would eat a whole beat")
    clips = media_dir(prod, unit, "clips")
    cuts = media_dir(prod, unit, "cuts")
    seg_dir = cuts / f"{name}_segments"
    master_audio = (prod / ident.AUDIO["master"]) if ident.AUDIO.get("master") else None
    own_audio = master_audio is None

    trans_note = f", {transition}f dissolve" if transition else ", hard cuts"
    print(f"SRC table for {name} (head {head} f, {'master audio' if master_audio else 'clip audio'}{trans_note}):")
    total = 0
    plan = []
    for i, (s, label) in enumerate(zip(srcs, names)):
        src = clips / s["file"]
        if not src.is_file():
            raise Refuse(f"slot {i+1:02d} {s['beat']}: {src} missing")
        if "__rej_" in src.name:
            raise Refuse(f"slot {i+1:02d} {s['beat']}: {src.name} is rejected")
        have = landed.probe(src)["frames"] or 0
        need = head + s["frames"]
        if have < need:
            raise Refuse(f"slot {i+1:02d} {s['beat']}: {src.name} has {have} frames, needs head {head} + {s['frames']} = {need}")
        total += s["frames"]
        plan.append({"slot": i + 1, "beat": s["beat"], "label": label, "job": s["job"], "src": str(src),
                     "src_frames": have, "head": head, "frames": s["frames"], "end_frame": total})
        print(f"  {i+1:02d}  {s['beat']:10} {s['frames']:4d} f  <- {src.name}  ({s['job']}, {have} f)   # {label}")
    print(f"  total {total} frames = {total / FPS:.3f} s")
    if dry:
        print("\ndry run — nothing built")
        return 0

    if seg_dir.exists():
        shutil.rmtree(seg_dir)          # the cut's own segments only; never a render
    seg_dir.mkdir(parents=True)
    # A board can mix graph families with different native output geometry (mm_clip_v1 sizes from
    # its ref; mm_chain_v1 is fixed 960x544) -- stream-copy concat silently accepts mismatched
    # segment resolutions without erroring (measured 2026-08-24: cutqc caught it after the fact,
    # nothing in assemble.py had refused). Canvas = the LARGEST source resolution on this board (by
    # pixel area), so no beat's own resolution is ever needlessly thrown away to match a smaller
    # one just because it happens to be more common; every segment scales to it explicitly, even
    # ones that already match (a no-op scale costs nothing and keeps one code path instead of two).
    sizes = Counter((landed.probe(clips / s["file"])["width"], landed.probe(clips / s["file"])["height"]) for s in srcs)
    canvas_w, canvas_h = max(sizes, key=lambda wh: wh[0] * wh[1])
    native = sum(c for wh, c in sizes.items() if wh == (canvas_w, canvas_h))
    print(f"  canvas {canvas_w}x{canvas_h} ({native}/{len(srcs)} beats native; others upscaled)")
    lst = []
    for p in plan:
        seg = seg_dir / f"seg_{p['slot']:02d}.mp4"
        vf = (f"trim=start_frame={head}:end_frame={head + p['frames']},setpts=PTS-STARTPTS,"
              f"fps={FPS},scale={canvas_w}:{canvas_h},format=yuv420p")
        # Video-only segments: audio in a segment gives the concat an edit-list offset and a
        # non-monotonic DTS at the first boundary (measured 2026-08-23: 933 frames read as 934).
        run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-i", p["src"], "-vf", vf, "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-video_track_timescale", "24000", str(seg)])
        if own_audio:
            t0, t1 = head / FPS, (head + p["frames"]) / FPS
            wav = seg.with_suffix(".wav")
            # H3's own audio track is not always frame-tight to its video length (measured
            # 2026-08-23: a 209-frame clip's audio ran 8.3ms short of the requested atrim window) --
            # apad to the exact requested duration so every segment is sample-accurate regardless of
            # what the source actually delivered; never let cutqc's audio-vs-picture check be the
            # thing papering over a short segment.
            run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-i", p["src"], "-vn",
                 "-af", f"atrim=start={t0}:end={t1},asetpts=PTS-STARTPTS,apad=whole_dur={t1 - t0:.6f}",
                 "-c:a", "pcm_s16le", "-ar", "48000", str(wav)])
            p["audio_segment"] = str(wav)
        got = landed.probe(seg)["frames"]
        if got != p["frames"]:
            raise Refuse(f"segment {seg.name} encoded {got} frames, wanted {p['frames']}")
        p["segment"] = str(seg)
        lst.append(seg)
        print(f"built     {seg.name}: {got} f")

    picture = cuts / f"{name}_picture.mp4"
    transition_meta = {"type": "cut", "frames": 0, "boundaries": []}
    if transition:
        final_total, boundaries = build_xfade_video(lst, [p["frames"] for p in plan], transition, picture)
        transition_meta = {"type": "dissolve", "frames": transition, "boundaries": boundaries}
    else:
        listfile = seg_dir / "concat.txt"
        listfile.write_text("".join(f"file '{s.as_posix()}'\n" for s in lst), encoding="utf-8")
        run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(picture)])
        final_total = total

    out = cuts / f"{name}.mp4"
    dur = final_total / FPS
    if master_audio:
        audio_src = master_audio
    elif transition:
        wavs = [Path(p["audio_segment"]) for p in plan]
        audio_src = seg_dir / "audio.wav"
        build_xfade_audio(wavs, [p["frames"] for p in plan], transition, audio_src)
    else:
        alist = seg_dir / "concat_audio.txt"
        alist.write_text("".join(f"file '{Path(p['audio_segment']).as_posix()}'\n" for p in plan), encoding="utf-8")
        audio_src = seg_dir / "audio.wav"
        run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(alist), "-c", "copy", str(audio_src)])
    run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-i", str(picture), "-i", str(audio_src),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
         "-af", f"atrim=0:{dur:.6f},asetpts=PTS-STARTPTS", "-movflags", "+faststart", str(out)])
    info = landed.probe(out)

    # tag_end_frame: where a slot's on-screen label should stop — the transition midpoint when
    # dissolving, the plain cumulative sum on a hard cut (degenerates to the old end_frame exactly).
    cum, tag_ends = 0, []
    for i, p in enumerate(plan):
        cum += p["frames"]
        if transition and i < len(plan) - 1:
            cum -= transition
            tag_ends.append(round(cum + transition / 2))
        else:
            tag_ends.append(cum)
    for p, t in zip(plan, tag_ends):
        p["end_frame"] = t

    meta = {"cut": name, "production": prod.name, "unit": unit.name if unit != prod else None, "fps": FPS,
            "head": head, "total_frames": final_total, "audio": str(master_audio) if master_audio else "clip",
            "transition": transition_meta,
            "master": str(out), "slots": plan, "LEN": [p["frames"] for p in plan], "SRC": [Path(p["src"]).name for p in plan]}
    (cuts / f"{name}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nassembled {out}: {info['frames']} f {info['width']}x{info['height']} {info['duration']:.3f} s; table {name}.json")
    if info["frames"] != final_total:
        raise Refuse(f"master has {info['frames']} frames, expected {final_total}" +
                     (f" ({total} beats sum - {(len(plan)-1)*transition} f transition overlap)" if transition else f" (beats sum {total})"))
    return 0


def build_xfade_video(segs: list[Path], frames: list[int], D: int, out: Path) -> tuple[int, list[int]]:
    """Chain xfade across all segments. offset_k = duration(merged_k) - D, in seconds
    (duration(merged_k) = sum(frames[:k+1]) - k*D frames — each prior xfade already ate D frames)."""
    n = len(segs)
    inputs: list[str] = []
    for s in segs:
        inputs += ["-i", str(s)]
    filt = []
    prev = "[0:v]"
    cum = frames[0]
    boundaries = []
    for k in range(1, n):
        off_frames = cum - D
        boundaries.append(off_frames)
        out_lbl = f"[v{k}]"
        filt.append(f"{prev}[{k}:v]xfade=transition=fade:duration={D / FPS:.6f}:offset={off_frames / FPS:.6f}{out_lbl}")
        cum = cum + frames[k] - D
        prev = out_lbl
    final_lbl = prev.strip("[]")
    run([str(paths.FFMPEG), "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
         "-map", f"[{final_lbl}]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
         "-pix_fmt", "yuv420p", "-video_track_timescale", "24000", str(out)])
    return cum, boundaries


def build_xfade_audio(wavs: list[Path], frames: list[int], D: int, out: Path) -> None:
    n = len(wavs)
    inputs: list[str] = []
    for w in wavs:
        inputs += ["-i", str(w)]
    filt = []
    prev = "[0:a]"
    for k in range(1, n):
        out_lbl = f"[a{k}]"
        filt.append(f"{prev}[{k}:a]acrossfade=d={D / FPS:.6f}:c1=tri:c2=tri{out_lbl}")
        prev = out_lbl
    final_lbl = prev.strip("[]")
    run([str(paths.FFMPEG), "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt),
         "-map", f"[{final_lbl}]", "-c:a", "pcm_s16le", "-ar", "48000", str(out)])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug"); ap.add_argument("unit"); ap.add_argument("name")
    ap.add_argument("--head", type=int, default=24); ap.add_argument("--transition", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    prod = skeleton.PRODUCTIONS / a.slug
    unit = prod if a.unit == "." else prod / a.unit
    try:
        return assemble(prod, unit, a.name, a.head, a.transition, a.dry_run)
    except Refuse as e:
        print(f"\nREFUSE: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
