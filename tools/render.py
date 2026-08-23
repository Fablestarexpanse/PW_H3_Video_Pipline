"""render.py — a job is a row, not a file (spec §7b).

  python tools/render.py <slug> <unit|.> <job_id> [--dry-run] [--proof] [--requeue]
  python tools/render.py <slug> <unit|.> --all-queued [--dry-run]

Reads the row from <unit>/jobs.jsonl, loads the graph FRESH from workflows/<graph>.api.json
(the committed API form of the frozen UI graph), and submits it to the local ComfyUI
HTTP API. It can only (a) set widget values and (b) leave unused ref slots out, which is
exactly what bypassing their LoadImage/LoadAudio nodes produces (proven 2026-08-22).
There is no code path that adds, renames or rewires a node.

Before queueing it refuses when: graph not in routing.md · contract.py fails · a ref is
not *_APPROVED_* (unless --proof, once per production) · a ref/audio/source file is
missing · frames off 17k+5 · seed not a non-negative int · preflight refuses the line ·
ComfyUI rejects the prompt (node_errors printed verbatim). Never calls save_workflow.

Row schemas (jobs.jsonl, one JSON object per line; `status` queued|landed|rejected):
  mm_clip  {"id","graph":"mm_clip_v1","lines":"x.lines","line":3,"refs":{"0":"refs/a_APPROVED_1.png",...},
            "audio":{"0":"audio/beat03_vocals.wav"},"frames":311,"seed":850003,"prefix":"..."}
  mm_image {"id","graph":"mm_image_v1","lines","line","lora":"<lora:..>","negpip":"(x:-1.2)","seed","width","height","prefix"}
  mm_edit  {"id","graph":"mm_edit_v1","source":"refs/a_APPROVED_1.png","prompt":"...","seed","prefix"}
  mm_chain {"id","graph":"mm_chain_v1","plan":{...},"run_name","fingerprint","refs":{...},"cond_audio","mux_audio","base_seed"}
Paths are relative to the production folder, or absolute (drive candidates for --proof).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402
import preflight  # noqa: E402
import skeleton  # noqa: E402

COMFY_URL = "http://127.0.0.1:8188"
CLIENT_ID = "moviemaker-v2"

# Node ids per frozen graph version. Versioned with the graph; a new graph version adds a row.
GRAPHS = {
    "mm_clip_v1": {
        "h3": "136", "lines": "156", "seed": "129", "prefix": "92",
        "refs": {0: "137", 1: "151", 2: "152", 3: "153", 4: "154", 5: "155", 6: "159", 7: "160", 8: "161"},
        "audio": {0: "150", 1: "162", 2: "163"},
    },
    "mm_image_v1": {"lines": "103", "seed": "14", "prefix": "18", "lora": "7", "negpip": "97", "size": "15"},
    "mm_edit_v1": {"source": "1", "prompt": "2", "seed": "16", "prefix": "19"},
    "mm_chain_v1": {
        "h3": "110", "plan": "1700", "cond_audio": "1926", "mux_audio": "940",
        "refs": {0: "911", 1: "1927", 2: "1928", 3: "1929", 4: "1930", 5: "1931", 6: "1932", 7: "1933", 8: "1934"},
    },
}
GRAPH_RE = re.compile(r"`(mm_(?:image|edit|clip|chain)_v\d+)`")


class Refuse(Exception):
    pass


def routed() -> set[str]:
    return set(GRAPH_RE.findall((paths.REPO / "routing.md").read_text(encoding="utf-8")))


def read_rows(jobs: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(jobs.read_text(encoding="utf-8").splitlines()):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise Refuse(f"{jobs} line {i}: not JSON ({e.msg})")
    return rows


def write_rows(jobs: Path, rows: list[dict]) -> None:
    jobs.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def resolve(prod: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else prod / p


def stage_input(prod: Path, rel: str, proof: bool, kind: str) -> str:
    """Copy a ref/audio/source into ComfyUI input/; return the basename the widget takes."""
    src = resolve(prod, rel)
    if not src.is_file():
        raise Refuse(f"{kind} {rel!r} does not exist")
    if "__rej_" in src.name:
        raise Refuse(f"{kind} {src.name} is a rejected render")
    if kind == "ref" and "_APPROVED_" not in src.name and not proof:
        raise Refuse(f"ref {src.name} is not *_APPROVED_* (a proof clip may use --proof once per production)")
    dst = paths.COMFY_INPUT / src.name
    if not dst.is_file() or dst.stat().st_size != src.stat().st_size:
        shutil.copyfile(src, dst)
        print(f"staged    {src.name} -> input/")
    return src.name


def drop_slot(api: dict, g: dict, node_key: str, slot_map: dict, prefix: str, used: set[int]) -> None:
    """Bypass semantics: remove the unused loader node and its slot on the H3 node."""
    for slot, nid in slot_map.items():
        if slot not in used:
            api.pop(nid, None)
            api[g["h3"]]["inputs"].pop(f"{prefix}_{slot}", None)


def build(prod: Path, unit: Path, row: dict, proof: bool) -> dict:
    graph = row.get("graph", "")
    if graph not in routed():
        raise Refuse(f"graph {graph!r} is not in routing.md")
    if graph not in GRAPHS:
        raise Refuse(f"graph {graph!r} has no node map in render.py")
    g = GRAPHS[graph]
    api = json.loads((paths.REPO / "workflows" / f"{graph}.api.json").read_text(encoding="utf-8"))
    prefix = row.get("prefix") or f"MovieMaker/{prod.name}/{unit.name if unit != prod else 'film'}/{row['id']}"

    if graph.startswith("mm_clip"):
        seed, frames = row.get("seed"), row.get("frames")
        if not isinstance(seed, int) or seed < 0:
            raise Refuse(f"seed {seed!r} must be a non-negative int (never randomize)")
        if not isinstance(frames, int) or frames < 5 or (frames - 5) % 17:
            raise Refuse(f"frames {frames!r} not on the 17k+5 grid")
        lf = unit / "prompts" / row["lines"]
        if not lf.is_file():
            raise Refuse(f"line file {lf} missing")
        rc = preflight.check_line_file(lf, None if proof else preflight.approved_from_identity(prod.name), preflight.DEFAULT_MAX_BLOCKS, row["line"])
        if rc:
            raise Refuse(f"preflight refused {lf.name}[{row['line']}]")
        refs = {int(k): v for k, v in row.get("refs", {}).items()}
        if 0 not in refs:
            raise Refuse("refs must include slot 0 — the master ref that sets the clip size")
        for slot, rel in refs.items():
            api[g["refs"][slot]]["inputs"]["image"] = stage_input(prod, rel, proof, "ref")
        audio = {int(k): v for k, v in row.get("audio", {}).items()}
        for slot, rel in audio.items():
            api[g["audio"][slot]]["inputs"]["audio"] = stage_input(prod, rel, proof, "audio")
        drop_slot(api, g, "h3", g["refs"], "ref_images.ref_image", set(refs))
        drop_slot(api, g, "h3", g["audio"], "ref_audios.ref_audio", set(audio))
        api[g["lines"]]["inputs"]["file_path"] = str(lf)
        api[g["lines"]]["inputs"]["index"] = int(row["line"])
        api[g["h3"]]["inputs"]["length"] = frames
        api[g["seed"]]["inputs"]["noise_seed"] = seed
        api[g["prefix"]]["inputs"]["filename_prefix"] = prefix

    elif graph.startswith("mm_image"):
        seed = row.get("seed")
        if not isinstance(seed, int) or seed < 0:
            raise Refuse(f"seed {seed!r} must be a non-negative int")
        lf = unit / "prompts" / row["lines"]
        if not lf.is_file():
            raise Refuse(f"line file {lf} missing")
        rc = preflight.check_line_file(lf, None, preflight.DEFAULT_MAX_BLOCKS, row["line"])
        if rc:
            raise Refuse(f"preflight refused {lf.name}[{row['line']}]")
        w, h = int(row.get("width", 0)), int(row.get("height", 0))
        if w % 8 or h % 8 or w < 256 or h < 256:
            raise Refuse(f"size {w}x{h} must be multiples of 8 and >= 256")
        api[g["lines"]]["inputs"]["file_path"] = str(lf)
        api[g["lines"]]["inputs"]["index"] = int(row["line"])
        api[g["seed"]]["inputs"]["value"] = seed
        api[g["size"]]["inputs"]["width"], api[g["size"]]["inputs"]["height"] = w, h
        # The graph ships with NO LoRA and NO NegPip line: the stack is identity.STYLE_STACK (spec §2),
        # a row may override it; NegPip is per job and empty unless the row says otherwise.
        ident = skeleton.load_identity(prod)
        api[g["lora"]]["inputs"]["value"] = row.get("lora", " ".join(getattr(ident, "STYLE_STACK", [])))
        api[g["negpip"]]["inputs"]["value"] = row.get("negpip", "")
        api[g["prefix"]]["inputs"]["filename_prefix"] = prefix

    elif graph.startswith("mm_edit"):
        seed = row.get("seed")
        if not isinstance(seed, int) or seed < 0:
            raise Refuse(f"seed {seed!r} must be a non-negative int")
        if not row.get("prompt", "").strip():
            raise Refuse("edit prompt is blank")
        pr = preflight.check_prompt(row["prompt"], row["id"], None, preflight.DEFAULT_MAX_BLOCKS)
        if pr.report():
            raise Refuse("preflight refused the edit prompt")
        api[g["source"]]["inputs"]["image"] = stage_input(prod, row["source"], True, "source")
        api[g["prompt"]]["inputs"]["value"] = row["prompt"]
        api[g["seed"]]["inputs"]["noise_seed"] = seed
        api[g["prefix"]]["inputs"]["filename_prefix"] = prefix

    elif graph.startswith("mm_chain"):
        plan = row.get("plan")
        if not isinstance(plan, dict) or not plan.get("shots"):
            raise Refuse("plan must be a dict with shots[]")
        for k in plan:
            if k not in ("prompt_prefix", "defaults", "shots"):
                raise Refuse(f"plan key {k!r} is a Plan-node widget, not a plan_json key")
        for i, shot in enumerate(plan["shots"]):
            text = shot["prompt"] if isinstance(shot["prompt"], str) else "\n".join(shot["prompt"])
            text = (plan.get("prompt_prefix", "") + "\n" + text).strip()
            if preflight.check_prompt(text, f"{row['id']}/shot{i}", None if proof else preflight.approved_from_identity(prod.name), preflight.DEFAULT_MAX_BLOCKS).report():
                raise Refuse(f"preflight refused plan shot {i}")
        if not row.get("run_name") or not row.get("fingerprint"):
            raise Refuse("run_name and fingerprint are required (checkpoints and resume depend on them)")
        if not isinstance(row.get("base_seed"), int):
            raise Refuse("base_seed must be an int")
        refs = {int(k): v for k, v in row.get("refs", {}).items()}
        if 0 not in refs:
            raise Refuse("refs must include slot 0")
        for slot, rel in refs.items():
            api[g["refs"][slot]]["inputs"]["image"] = stage_input(prod, rel, proof, "ref")
        drop_slot(api, g, "h3", g["refs"], "ref_images.ref_image", set(refs))
        api[g["cond_audio"]]["inputs"]["audio"] = stage_input(prod, row["cond_audio"], True, "audio")
        api[g["mux_audio"]]["inputs"]["audio"] = stage_input(prod, row["mux_audio"], True, "audio")
        p = api[g["plan"]]["inputs"]
        p["plan_json"] = json.dumps(plan, ensure_ascii=False, indent=2)
        p["run_name"], p["generation_fingerprint"], p["base_seed"] = row["run_name"], row["fingerprint"], row["base_seed"]
    else:
        raise Refuse(f"unknown graph family {graph}")
    return api


def submit(api: dict) -> str:
    body = json.dumps({"prompt": api, "client_id": CLIENT_ID}).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise Refuse(f"ComfyUI rejected the prompt ({e.code}):\n{detail}")
    except urllib.error.URLError as e:
        raise Refuse(f"ComfyUI unreachable at {COMFY_URL}: {e.reason}")
    if resp.get("node_errors"):
        raise Refuse("ComfyUI node_errors:\n" + json.dumps(resp["node_errors"], indent=1))
    return resp["prompt_id"]


def run_job(prod: Path, unit: Path, row: dict, rows: list[dict], jobs: Path, dry: bool, proof: bool, requeue: bool) -> int:
    if row.get("status") == "queued" and row.get("prompt_id") and not requeue:
        raise Refuse(f"{row['id']} is already queued as {row['prompt_id']} (use --requeue)")
    if row.get("status") == "landed" and not requeue:
        raise Refuse(f"{row['id']} already landed (use --requeue to re-render)")
    if proof:
        prior = [r for u in skeleton.units(prod, skeleton.load_identity(prod).FORMAT)
                 for r in read_rows(u / "jobs.jsonl") if r.get("proof") and r["id"] != row["id"]]
        if prior:
            raise Refuse(f"a proof clip already exists for this production: {prior[0]['id']} — one per production")
    r = subprocess.run([sys.executable, str(paths.REPO / "tools" / "contract.py"), prod.name], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        print(r.stdout)
        raise Refuse("contract.py refused")
    api = build(prod, unit, row, proof)
    print(f"resolved  {row['id']} on {row['graph']}: {len(api)} nodes, " +
          ", ".join(f"{k}={row[k]!r}" for k in ("line", "frames", "seed", "base_seed") if k in row))
    if dry:
        print(json.dumps(api, indent=1, ensure_ascii=False))
        print("\ndry run — not submitted")
        return 0
    pid = submit(api)
    row.update({"status": "queued", "prompt_id": pid, "proof": bool(proof) or row.get("proof", False)})
    write_rows(jobs, rows)
    print(f"queued    {row['id']} -> prompt_id {pid}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug"); ap.add_argument("unit"); ap.add_argument("job", nargs="?")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--proof", action="store_true")
    ap.add_argument("--requeue", action="store_true"); ap.add_argument("--all-queued", action="store_true")
    a = ap.parse_args(argv)
    prod = skeleton.PRODUCTIONS / a.slug
    unit = prod if a.unit == "." else prod / a.unit
    jobs = unit / "jobs.jsonl"
    try:
        if not jobs.is_file():
            raise Refuse(f"{jobs} not found")
        rows = read_rows(jobs)
        if a.all_queued:
            todo = [r for r in rows if r.get("status") in (None, "", "new") or (r.get("status") == "queued" and not r.get("prompt_id"))]
        else:
            todo = [r for r in rows if r.get("id") == a.job]
            if not todo:
                raise Refuse(f"no row with id {a.job!r} in {jobs}")
        rc = 0
        for row in todo:
            rc |= run_job(prod, unit, row, rows, jobs, a.dry_run, a.proof, a.requeue)
        return rc
    except Refuse as e:
        print(f"\nREFUSE: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
