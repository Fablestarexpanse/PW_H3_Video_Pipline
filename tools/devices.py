"""devices.py — named transition library for assemble.py, not an if/elif ladder.

Adding a transition is adding one dict entry here, never editing assemble.py's
filter-graph code. Each device names an ffmpeg `xfade` transition type (video)
and an `acrossfade` curve (audio) — ffmpeg ships dozens of xfade types built
in, so the library is a lookup table, not new compositing code.

    python tools/devices.py                    # list every device
    python tools/devices.py --sheet [out.mp4]  # demo clip: two colour cards,
                                                # one transition per device in
                                                # turn, labelled — so you can SEE
                                                # a device before spending a real
                                                # beat on it (assemble.py --device)

Used by: `assemble.py --transition N --device NAME` (NAME defaults to "dissolve",
the prior hardcoded behaviour). "cut" is not a device — it is transition=0.

The idea — a named, pluggable transition library instead of an if/elif ladder in the assembler —
comes from `devices.py` in Garrett Bloome's rtome-showrunner-pipeline
(github.com/KerbalTheGathering/rtome-showrunner-pipeline), a sibling ComfyUI production pipeline.
His devices are hand-written PIL compositing functions; ours is a lookup table into ffmpeg's own
built-in xfade transition catalog, since ffmpeg is already load-bearing in this stack — a
different implementation for the same shape of problem, not a port of his code.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402

FPS = 24

# name -> ffmpeg xfade transition type, acrossfade curve. Full xfade list:
# https://ffmpeg.org/ffmpeg-filters.html#xfade — this is a starting set, not
# the whole catalog; add more by adding rows, not code.
DEVICES: dict[str, dict] = {
    "dissolve":   {"xfade": "fade",       "audio": "tri", "note": "even cross-dissolve — the prior hardcoded default"},
    "whip":       {"xfade": "hblur",      "audio": "tri", "note": "fast horizontal blur — reads as a whip-pan cut"},
    "flash":      {"xfade": "fadewhite",  "audio": "tri", "note": "flash to white and back — hard-hit chorus punctuation"},
    "flashblack": {"xfade": "fadeblack",  "audio": "tri", "note": "flash to black and back — heavier, more ominous"},
    "wipe_left":  {"xfade": "wipeleft",   "audio": "tri", "note": "hard-edge wipe, right to left"},
    "wipe_right": {"xfade": "wiperight",  "audio": "tri", "note": "hard-edge wipe, left to right"},
    "slide_up":   {"xfade": "slideup",    "audio": "tri", "note": "incoming slides up over outgoing"},
    "circle":     {"xfade": "circleopen", "audio": "tri", "note": "circle iris opening on the incoming frame"},
    "pixelize":   {"xfade": "pixelize",   "audio": "tri", "note": "outgoing breaks into blocks before the incoming resolves"},
    "smooth":     {"xfade": "smoothleft", "audio": "tri", "note": "soft directional wipe, gentler edge than wipe_left"},
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def _font() -> str | None:
    """ffmpeg filter-graph-safe font path: forward slashes, drive colon escaped
    (a bare 'C:\\...' collides with the filter option separator and the backslash
    escape character both — measured on Windows, ffmpeg refuses the filterchain)."""
    for f in FONT_CANDIDATES:
        if Path(f).is_file():
            return f.replace("\\", "/").replace(":", "\\:")
    return None


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd[:6])}…\n{r.stderr[-800:]}")


def list_devices() -> None:
    print(f"{len(DEVICES)} device(s):")
    for name, d in DEVICES.items():
        print(f"  {name:12} xfade={d['xfade']:12} audio={d['audio']:4}  {d['note']}")
    print("\n'cut' is not a device — it is assemble.py's default (--transition 0, stream-copy, no re-encode).")


def build_sheet(out: Path, w: int = 640, h: int = 360, card_s: float = 2.0) -> None:
    font = _font()
    if not font:
        print("advise    no arial.ttf found under C:/Windows/Fonts — sheet will render without labels")
    names = list(DEVICES.keys())
    per_device: list[Path] = []
    tmp = out.parent / f"{out.stem}_parts"
    tmp.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(names):
        d = DEVICES[name]
        D = 0.75
        seg = tmp / f"{i:02d}_{name}.mp4"
        label_a = f"drawtext=text='{name} A':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2" + (f":fontfile='{font}'" if font else "")
        label_b = f"drawtext=text='{name} B':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2" + (f":fontfile='{font}'" if font else "")
        filt = (
            f"color=c=steelblue:s={w}x{h}:d={card_s}:r={FPS}[a0];[a0]{label_a}[a];"
            f"color=c=indianred:s={w}x{h}:d={card_s}:r={FPS}[b0];[b0]{label_b}[b];"
            f"[a][b]xfade=transition={d['xfade']}:duration={D}:offset={card_s - D}[v]"
        )
        run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "nullsrc",
             "-filter_complex", filt, "-map", "[v]", "-t", str(card_s * 2 - D),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(seg)])
        per_device.append(seg)
    listfile = tmp / "concat.txt"
    listfile.write_text("".join(f"file '{p.as_posix()}'\n" for p in per_device), encoding="utf-8")
    run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listfile), "-c", "copy", str(out)])
    print(f"sheet     {len(names)} device(s) -> {out}")
    print(f"          order: {', '.join(names)}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--sheet", nargs="?", const="__default__")
    a = ap.parse_args(argv)
    if a.sheet is None:
        list_devices()
        return 0
    out = Path(a.sheet) if a.sheet != "__default__" else paths.REPO / "out" / "devices_sheet.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    build_sheet(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
