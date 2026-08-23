"""costs.py — every cost is a measured row; G5 cannot quote what was not measured (spec §3).

  python tools/costs.py ingest <slug>            add a row for every landed render in renders.jsonl
                                                 that has minutes and no costs row yet
  python tools/costs.py quote --graph mm_clip_v1 --frames 311 [--res 1344x768]
                                                 print the measured rows for that regime; refuse if none
  python tools/costs.py table                    print costs.csv

costs.csv columns: frames,res,regime,refs,minutes,date,production,graph,job
regime = graph version + steps (e.g. mm_clip_v1/20). Minutes come from ComfyUI's own
execution_start/execution_success timestamps, recorded by landed.py — never typed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402
import skeleton  # noqa: E402

CSV = paths.REPO / "costs.csv"
FIELDS = ["frames", "res", "regime", "refs", "minutes", "date", "production", "graph", "job"]
STEPS = {"mm_clip_v1": 20, "mm_image_v1": 11, "mm_edit_v1": 4, "mm_chain_v1": 20}


def rows() -> list[dict]:
    with CSV.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("frames")]


def write(all_rows: list[dict]) -> None:
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def ingest(slug: str) -> int:
    prod = skeleton.PRODUCTIONS / slug
    existing = rows()
    by_job = {(r["production"], r["job"]): r for r in existing}
    # A job id can be re-rendered (proof iteration, --requeue) leaving several renders.jsonl rows
    # under the same id; keep the LATEST landed one, not the first (measured 2026-08-23: a stale
    # first-attempt cost survived three re-renders because ingest only ever skipped-if-present).
    latest: dict[str, dict] = {}
    for line in (prod / "renders.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") != "landed" or not r.get("minutes"):
            continue
        if r["job"] not in latest or r["landed"] > latest[r["job"]]["landed"]:
            latest[r["job"]] = r
    added = updated = 0
    for job, r in latest.items():
        key = (slug, job)
        g = r["graph"]
        unit = prod if r.get("unit") is None else prod / r["unit"]
        refs = ""
        for jl in (unit / "jobs.jsonl").read_text(encoding="utf-8").splitlines():
            if jl.strip() and json.loads(jl).get("id") == job:
                refs = str(len(json.loads(jl).get("refs", {})))
        row = {"frames": r.get("frames") or 1, "res": f"{r['width']}x{r['height']}",
               "regime": f"{g}/{STEPS.get(g, '?')}", "refs": refs, "minutes": r["minutes"],
               "date": r["landed"][:10], "production": slug, "graph": g, "job": job}
        if key in by_job:
            if by_job[key] != row:
                by_job[key].update(row)
                updated += 1
                print(f"updated   {job}: {r.get('frames')} f {r['width']}x{r['height']} {r['minutes']} min")
        else:
            existing.append(row)
            by_job[key] = row
            added += 1
            print(f"added     {job}: {r.get('frames')} f {r['width']}x{r['height']} {r['minutes']} min")
    write(existing)
    print(f"measured  {added} new row(s), {updated} updated; costs.csv now {len(existing)}")
    return 0


def quote(graph: str, frames: int, res: str | None) -> int:
    match = [r for r in rows() if r["graph"] == graph and int(r["frames"]) == frames and (not res or r["res"] == res)]
    if not match:
        tail = f" {res}" if res else ""
        print(f"REFUSE: no measured cost row for {graph} at {frames} frames{tail} — render the proof clip at the shipped length first; cost is superlinear, never extrapolate")
        return 1
    mins = [float(r["minutes"]) for r in match]
    for r in match:
        print(f"measured  {r['date']} {r['production']}/{r['job']}: {r['frames']} f {r['res']} {r['regime']} refs {r['refs']} -> {r['minutes']} min")
    print(f"\nquote     {graph} @ {frames} f: {min(mins):.2f}-{max(mins):.2f} min per clip over {len(match)} measurement(s)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("cmd"); ap.add_argument("slug", nargs="?")
    ap.add_argument("--graph"); ap.add_argument("--frames", type=int); ap.add_argument("--res")
    a = ap.parse_args(argv)
    if a.cmd == "ingest" and a.slug:
        return ingest(a.slug)
    if a.cmd == "quote" and a.graph and a.frames:
        return quote(a.graph, a.frames, a.res)
    if a.cmd == "table":
        for r in rows():
            print("  ".join(f"{k}={r[k]}" for k in FIELDS if r.get(k)))
        print(f"measured  {len(rows())} row(s)")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
