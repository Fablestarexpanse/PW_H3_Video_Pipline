"""deploy.py — push the frozen graphs from the repo into ComfyUI's workflow folder.

The repo is the source of truth (spec §7a). The deployed copy is overwritten
from here, never edited in place. `drift.py` refuses when a deployed hash
differs from the repo.

  python workflows/deploy.py            deploy every mm_*_v<n>.json, verify hashes
  python workflows/deploy.py --check    verify only (exit 1 on any mismatch / missing)
  python workflows/deploy.py --archive  move every non-mm_ workflow on the instance
                                        into <workflows>/archive/ (never deletes)

Exits 1 if any graph fails to deploy or verify.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

# Windows consoles default to cp1252; workflow names contain em-dashes and macrons.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import paths  # noqa: E402

HERE = Path(__file__).resolve().parent
GRAPH_RE = re.compile(r"^mm_(image|edit|clip|chain|ifl)_v\d+\.json$")
ASSETS = ("null_ref.png", "null_ref.wav")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def repo_graphs() -> list[Path]:
    return sorted(p for p in HERE.glob("mm_*.json") if GRAPH_RE.match(p.name))


VIRTUAL = {"MarkdownNote", "Note", "Reroute", "PrimitiveNode"}


def api_matches_ui(src: Path) -> str | None:
    """The committed .api.json must cover exactly the UI graph's real, non-muted nodes."""
    api_p = src.with_suffix("").with_suffix(".api.json")
    if not api_p.is_file():
        return f"{api_p.name} missing"
    ui = json.loads(src.read_text(encoding="utf-8"))
    api = json.loads(api_p.read_text(encoding="utf-8"))
    ui_ids = {str(n["id"]) for n in ui["nodes"] if n["type"] not in VIRTUAL and n.get("mode", 0) == 0}
    api_ids = set(api)
    if ui_ids != api_ids:
        return f"{api_p.name} nodes differ from {src.name}: only-ui {sorted(ui_ids - api_ids)} only-api {sorted(api_ids - ui_ids)}"
    for n in ui["nodes"]:
        if str(n["id"]) in api and api[str(n["id"])]["class_type"] != n["type"]:
            return f"{api_p.name} node {n['id']} class {api[str(n['id'])]['class_type']} != {n['type']}"
    return None


def check() -> int:
    bad = 0
    for src in repo_graphs():
        err = api_matches_ui(src)
        if err:
            print(f"DIFFERS   {err}")
            bad += 1
        dst = paths.COMFY_WORKFLOWS / src.name
        if not dst.is_file():
            print(f"MISSING   {src.name}  (not deployed)")
            bad += 1
        elif sha256(src) != sha256(dst):
            print(f"DIFFERS   {src.name}  repo {sha256(src)[:12]} != deployed {sha256(dst)[:12]}")
            bad += 1
        else:
            print(f"ok        {src.name}  {sha256(src)[:12]}")
    for a in ASSETS:
        src, dst = HERE / a, paths.COMFY_INPUT / a
        if not dst.is_file() or sha256(src) != sha256(dst):
            print(f"MISSING   input/{a}")
            bad += 1
        else:
            print(f"ok        input/{a}")
    if bad:
        print(f"\nREFUSE: {bad} deployed file(s) differ from the repo — run deploy.py")
        return 1
    print(f"\nall {len(repo_graphs())} graphs + {len(ASSETS)} assets match the repo")
    return 0


def deploy() -> int:
    graphs = repo_graphs()
    if not graphs:
        print("REFUSE: no mm_*_v<n>.json graphs in", HERE)
        return 1
    for src in graphs:
        json.loads(src.read_text(encoding="utf-8"))  # refuse on malformed JSON
        dst = paths.COMFY_WORKFLOWS / src.name
        shutil.copyfile(src, dst)
        print(f"deployed  {src.name} -> {dst}")
    for a in ASSETS:
        shutil.copyfile(HERE / a, paths.COMFY_INPUT / a)
        print(f"deployed  {a} -> {paths.COMFY_INPUT / a}")
    return check()


def archive() -> int:
    arch = paths.COMFY_WORKFLOWS / "archive"
    arch.mkdir(exist_ok=True)
    moved = 0
    for p in paths.COMFY_WORKFLOWS.iterdir():
        if p.is_file() and p.suffix == ".json" and not GRAPH_RE.match(p.name):
            target = arch / p.name
            if target.exists():
                print(f"REFUSE: {target} already exists; not overwriting")
                return 1
            shutil.move(str(p), str(target))
            print(f"archived  {p.name}")
            moved += 1
    print(f"\n{moved} workflow(s) moved to {arch}; nothing deleted")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--check"]:
        sys.exit(check())
    if args == ["--archive"]:
        sys.exit(archive())
    if args:
        print(__doc__)
        sys.exit(1)
    sys.exit(deploy())
