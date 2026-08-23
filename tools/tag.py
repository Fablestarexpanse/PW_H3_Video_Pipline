"""tag.py — the two review copies of a cut: slot-tagged, and 720p web (spec §3; Assembly Guide).

  python tools/tag.py <cut.json> [--font C:/Windows/Fonts/consola.ttf]

Burns onto a COPY (the master is never touched):
  top right    SLOT NN  <beat name>        under it   +Ns elapsed within the slot
  bottom left  running timecode M:SS
Writes <cut>_TAGGED.mp4 (854 wide, crf 26) and <cut>_web.mp4 (720 wide, crf 30, no tags;
the 30 MB delivery cap). Refuses if either output's frame count != the master's.
Slot boundaries come from the cut table's LEN (frames), so tags land on the exact frame.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import landed  # noqa: E402
import paths  # noqa: E402

DEFAULT_FONT = "C:/Windows/Fonts/consola.ttf"


def esc(s: str) -> str:
    return s.replace("\\", "").replace(":", "\\:").replace("'", "").replace("%", "").replace(",", " ")


def font_arg(font: str) -> str:
    return font.replace("\\", "/").replace(":", "\\:")


def tag_filter(meta: dict, font: str, big: int = 26, small: int = 20) -> str:
    fps = meta["fps"]
    f = font_arg(font)
    parts = []
    f0 = 0
    for slot in meta["slots"]:
        f1 = slot["end_frame"]; t0 = f0 / fps     # frame-based enable: exact at the boundary, no t rounding
        parts.append(f"drawtext=fontfile='{f}':text='SLOT {slot['slot']:02d}  {esc(slot['label'])}':x=w-tw-18:y=16:"
                     f"fontsize={big}:fontcolor=white@0.92:box=1:boxcolor=black@0.55:boxborderw=8:enable='between(n,{f0},{f1 - 1})'")
        parts.append(f"drawtext=fontfile='{f}':text='+%{{eif\\:t-{t0:.4f}\\:d}}s':x=w-tw-18:y={16 + big + 10}:"
                     f"fontsize={small}:fontcolor=white@0.75:box=1:boxcolor=black@0.45:boxborderw=6:enable='between(n,{f0},{f1 - 1})'")
        f0 = f1
    parts.append(f"drawtext=fontfile='{f}':text='%{{eif\\:t/60\\:d}}\\:%{{eif\\:mod(t\\,60)\\:d\\:2}}':x=18:y=h-th-16:"
                 f"fontsize={small}:fontcolor=white@0.75:box=1:boxcolor=black@0.45:boxborderw=6")
    return ",".join(parts)


def encode(src: Path, dst: Path, vf: str, crf: int) -> None:
    r = subprocess.run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-i", str(src), "-vf", vf,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", str(dst)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"REFUSE: ffmpeg failed for {dst.name}:\n{r.stderr[-800:]}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("cut"); ap.add_argument("--font", default=DEFAULT_FONT)
    a = ap.parse_args(argv)
    if not Path(a.font).is_file():
        print(f"REFUSE: font {a.font} not found"); return 1
    meta = json.loads(Path(a.cut).read_text(encoding="utf-8"))
    master = Path(meta["master"])
    mframes = landed.probe(master)["frames"]
    tagged = master.with_name(master.stem + "_TAGGED.mp4")
    web = master.with_name(master.stem + "_web.mp4")
    encode(master, tagged, "scale=854:-2," + tag_filter(meta, a.font), 26)
    encode(master, web, "scale=720:-2", 30)
    rc = 0
    for p in (tagged, web):
        fr = landed.probe(p)["frames"]
        size = p.stat().st_size / 1e6
        ok = fr == mframes
        print(f"{'ok      ' if ok else 'REFUSE  '}  {p.name}: {fr} f (master {mframes}), {size:.1f} MB{'' if size <= 30 or p is tagged else '  — over the 30 MB delivery cap'}")
        rc |= 0 if ok else 1
    meta["tagged"], meta["web"] = str(tagged), str(web)
    Path(a.cut).write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nREFUSE: tag" if rc else "\ntag passes")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
