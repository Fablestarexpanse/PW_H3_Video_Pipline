"""findings.py — a lesson is a check, or it did not happen (spec §0.8; G6).

  python tools/findings.py                       list; refuse if any count >= 2 is open with no check/fix/dropped
  python tools/findings.py check                 the G6 / drift form: faults only
  python tools/findings.py add "<text>" [--production slug]
                                                 append with count 1, or bump count if the same text exists
  python tools/findings.py promote <n> --check "tools/x.py code" | --fix "what changed" | --dropped "why"
  python tools/findings.py ratify <n>            Ronan has accepted a decision (status ratified)

Rows: {"finding", "count", "productions": [], "status": open|ratified|promoted, "check"|"fix"|"dropped"}.
The log holds WHY; git holds what.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402

F = paths.REPO / "findings.jsonl"


def load() -> list[dict]:
    out = []
    for i, line in enumerate(F.read_text(encoding="utf-8").splitlines()):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"REFUSE: findings.jsonl line {i + 1} is not JSON ({e.msg})")
    return out


def save(rows: list[dict]) -> None:
    F.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def promoted(r: dict) -> bool:
    return any(k in r for k in ("check", "fix", "dropped"))


def check(rows: list[dict], verbose: bool) -> int:
    bad = 0
    for i, r in enumerate(rows, 1):
        flag = r.get("count", 0) >= 2 and r.get("status") == "open" and not promoted(r)
        bad += flag
        if verbose or flag:
            tag = "UNPROMOTED" if flag else f"{r.get('status', 'open'):10}"
            print(f"{i:3d}  x{r.get('count', 1)}  {tag}  {r['finding'][:110]}")
    print(f"\nmeasured  {len(rows)} finding(s), {bad} at count >= 2 with no check/fix/dropped")
    if bad:
        print("REFUSE: promote or drop them before the next production (G6)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("cmd", nargs="?", default="list"); ap.add_argument("arg", nargs="?")
    ap.add_argument("--production"); ap.add_argument("--check"); ap.add_argument("--fix"); ap.add_argument("--dropped")
    a = ap.parse_args(argv)
    rows = load()
    if a.cmd == "list":
        return check(rows, True)
    if a.cmd == "check":
        return check(rows, False)
    if a.cmd == "add" and a.arg:
        for r in rows:
            if r["finding"].strip().lower() == a.arg.strip().lower():
                r["count"] = r.get("count", 1) + 1
                if a.production and a.production not in r.setdefault("productions", []):
                    r["productions"].append(a.production)
                save(rows)
                print(f"bumped    count -> {r['count']}: {r['finding'][:80]}")
                return 0
        rows.append({"finding": a.arg.strip(), "count": 1, "productions": [a.production] if a.production else [], "status": "open"})
        save(rows)
        print(f"added     #{len(rows)} count 1")
        return 0
    if a.cmd in ("promote", "ratify") and a.arg and a.arg.isdigit():
        i = int(a.arg) - 1
        if not 0 <= i < len(rows):
            print(f"REFUSE: no finding #{a.arg}"); return 1
        r = rows[i]
        if a.cmd == "ratify":
            r["status"] = "ratified"
        else:
            if not (a.check or a.fix or a.dropped):
                print("REFUSE: promote needs --check, --fix or --dropped"); return 1
            for k, v in (("check", a.check), ("fix", a.fix), ("dropped", a.dropped)):
                if v:
                    r[k] = v
            r["status"] = "promoted"
        save(rows)
        print(f"{a.cmd:9} #{a.arg}: {r['finding'][:80]}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
