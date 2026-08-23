"""landed.py — copy every finished render out of ComfyUI the moment it lands (spec §3).

  python tools/landed.py <slug> [<unit|.>]      poll every queued row once
  python tools/landed.py <slug> --watch [N]     poll every N s (default 30) until nothing is queued

For each jobs.jsonl row with status=queued and a prompt_id: read /history/<prompt_id>;
on success copy every output file to the drive (clips → <media>/<unit>/clips/, stills →
<media>/refs/candidates/), ffprobe it, write a 6-frame filmstrip to <unit>/filmstrips/,
append a renders.jsonl row, and set the job status.
Refuses (exit 1, row status=refused_frames) when a clip's frame count != row.frames.
Never deletes anything in ComfyUI's output/ — it is scratch, not a source.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402
import render  # noqa: E402
import skeleton  # noqa: E402

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm"}


def history(pid: str) -> dict | None:
    with urllib.request.urlopen(f"{render.COMFY_URL}/history/{pid}", timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get(pid)


def queue_state(pid: str) -> str:
    with urllib.request.urlopen(f"{render.COMFY_URL}/queue", timeout=30) as r:
        q = json.loads(r.read().decode("utf-8"))
    for item in q.get("queue_running", []):
        if item[1] == pid:
            return "running"
    for item in q.get("queue_pending", []):
        if item[1] == pid:
            return "pending"
    return "absent"


def probe(p: Path) -> dict:
    out = subprocess.run(
        [str(paths.FFPROBE), "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_read_frames,r_frame_rate:format=duration",
         "-of", "json", str(p)], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = (j.get("streams") or [{}])[0]
    return {"width": s.get("width"), "height": s.get("height"),
            "frames": int(s["nb_read_frames"]) if s.get("nb_read_frames") else None,
            "fps": s.get("r_frame_rate"), "duration": float(j.get("format", {}).get("duration", 0))}


def filmstrip(src: Path, dst: Path, frames: int) -> None:
    step = max(1, frames // 6)
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(paths.FFMPEG), "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", f"select='not(mod(n\\,{step}))',scale=320:-2,tile=6x1", "-frames:v", "1", str(dst)],
                   check=True)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def output_files(h: dict, row: dict) -> list[Path]:
    files = []
    for node_out in h.get("outputs", {}).values():
        for v in node_out.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and item.get("filename") and item.get("type", "output") == "output":
                        files.append(paths.COMFY_OUTPUT / item.get("subfolder", "") / item["filename"])
    if row.get("graph", "").startswith("mm_chain") and row.get("run_name"):
        final = paths.COMFY_OUTPUT / "h3_chain" / row["run_name"] / "final.mp4"
        if final.is_file():
            files.append(final)
    return [f for f in files if f.is_file()]


def land(prod: Path, unit: Path, row: dict) -> int:
    pid = row["prompt_id"]
    h = history(pid)
    if h is None:
        st = queue_state(pid)
        print(f"waiting   {row['id']} ({st})" if st != "absent" else f"LOST      {row['id']}: prompt {pid} is neither queued nor in history — render.py --requeue")
        return 0
    status = h.get("status", {})
    if status.get("status_str") == "error" or not status.get("completed", False):
        msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
        detail = msgs[0][1].get("exception_message", "") if msgs else json.dumps(status)[:300]
        row["status"] = "error"
        row["error"] = detail[:500]
        print(f"ERROR     {row['id']}: {detail[:300]}")
        return 1
    # wall-clock from ComfyUI's own timestamps (ms): execution_start -> execution_success
    ts = {m[0]: m[1].get("timestamp") for m in status.get("messages", []) if isinstance(m, list) and len(m) == 2 and isinstance(m[1], dict)}
    minutes = round((ts["execution_success"] - ts["execution_start"]) / 60000, 2) if ts.get("execution_success") and ts.get("execution_start") else None
    files = output_files(h, row)
    if not files:
        row["status"] = "error"
        row["error"] = "completed with no output files"
        print(f"ERROR     {row['id']}: completed with no output files")
        return 1

    slug = prod.name
    unit_name = unit.name if unit != prod else None
    rc = 0
    for src in files:
        is_video = src.suffix.lower() in VIDEO_EXT
        if is_video:
            dst_dir = paths.media_for(slug, *(([unit_name] if unit_name else []) + ["clips"]))
        else:
            dst_dir = paths.media_for(slug, "refs", "candidates")
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{row['id']}__{src.name}"
        if not dst.is_file():
            shutil.copyfile(src, dst)
        info = probe(dst)
        rec = {"job": row["id"], "unit": unit_name, "prompt_id": pid, "graph": row["graph"], "file": str(dst),
               "sha256": sha256(dst), "landed": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "seed": row.get("seed", row.get("base_seed")), "minutes": minutes, **info}
        if is_video:
            expected = int(row.get("frames", 0))
            strip = paths.media_for(slug, *(([unit_name] if unit_name else []) + ["filmstrips"])) / f"{row['id']}.png"
            filmstrip(dst, strip, info["frames"] or 1)
            rec["filmstrip"] = str(strip)
            rec["expected_frames"] = expected
            if expected and info["frames"] != expected:
                rec["status"] = "refused_frames"
                row["status"] = "refused_frames"
                print(f"REFUSE    {row['id']}: {info['frames']} frames != expected {expected} ({dst.name}); kept, filmstrip {strip.name}")
                rc = 1
            else:
                rec["status"] = "landed"
                print(f"landed    {row['id']}: {info['frames']} frames {info['width']}x{info['height']} {info['duration']:.3f}s -> {dst.name}; filmstrip {strip.name}")
        else:
            rec["status"] = "landed"
            print(f"landed    {row['id']}: {info['width']}x{info['height']} -> {dst.name}")
        with (prod / "renders.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if row["status"] != "refused_frames":
        row["status"] = "landed"
    row["landed_files"] = [str(paths.media_for(slug)) and f.name for f in files]
    return rc


def poll(prod: Path, units: list[Path]) -> tuple[int, int]:
    rc, pending = 0, 0
    for unit in units:
        jobs = unit / "jobs.jsonl"
        rows = render.read_rows(jobs)
        changed = False
        for row in rows:
            if row.get("status") == "queued" and row.get("prompt_id"):
                before = dict(row)
                rc |= land(prod, unit, row)
                if row != before:
                    changed = True
                if row.get("status") == "queued":
                    pending += 1
        if changed:
            render.write_rows(jobs, rows)
    return rc, pending


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    prod = skeleton.PRODUCTIONS / argv[0]
    ident = skeleton.load_identity(prod)
    units = skeleton.units(prod, ident.FORMAT)
    if len(argv) > 1 and argv[1] not in ("--watch",):
        units = [prod if argv[1] == "." else prod / argv[1]]
    watch = "--watch" in argv
    interval = int(argv[argv.index("--watch") + 1]) if watch and len(argv) > argv.index("--watch") + 1 and argv[-1].isdigit() else 30
    while True:
        rc, pending = poll(prod, units)
        print(f"measured  {pending} job(s) still queued")
        if not watch or pending == 0:
            return rc
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
