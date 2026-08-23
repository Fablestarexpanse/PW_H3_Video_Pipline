"""drift.py — productions cannot drift from the system (spec §5d).

  python tools/drift.py              every production + deployed graphs + findings
  python tools/drift.py <slug>       one production only
  python tools/drift.py --no-comfy   skip the deployed-hash check (no instance reachable)

Refuses (exit 1) when any production has:
  - a file not in the template skeleton, or a required file missing
  - template_version older than templates/TEMPLATE_VERSION (run migrate.py)
  - a .py other than identity.py, or an identity.py field the template does not declare
  - a prompt line whose <Picture N> is not a slot declared in identity CAST/LOCATIONS
  - a workflow name not in routing.md
or when a deployed ComfyUI graph's hash differs from workflows/ (deploy.py --check),
or when findings.jsonl has a finding at count >= 2 still open.
Runs in the pre-commit hook and at /start.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402
import skeleton  # noqa: E402

PIC_RE = re.compile(r"<Picture (\d+)>")
GRAPH_RE = re.compile(r"`(mm_(?:image|edit|clip|chain)_v\d+)`")


def check_production(prod: Path) -> int:
    faults = 0

    def fail(msg: str) -> None:
        nonlocal faults
        faults += 1
        print(f"DRIFT     {prod.name}: {msg}")

    try:
        ident = skeleton.load_identity(prod)
    except Exception as e:  # a broken identity.py is drift, not a crash
        print(f"DRIFT     {prod.name}: identity.py does not import: {e}")
        return 1
    fmt = getattr(ident, "FORMAT", "")
    if fmt not in ("film", "show"):
        fail(f"identity.FORMAT = {fmt!r}")
        fmt = "film"

    declared = {k for k in vars(ident) if k.isupper()}
    for extra in sorted(declared - set(skeleton.IDENTITY_FIELDS)):
        fail(f"identity.py declares undeclared field {extra}")
    for missing in sorted(set(skeleton.IDENTITY_FIELDS) - declared):
        fail(f"identity.py is missing field {missing}")

    tv_file = prod / "template_version"
    if not tv_file.is_file():
        fail("template_version missing")
    else:
        tv = int(tv_file.read_text(encoding="utf-8").strip() or 0)
        if tv < skeleton.template_version():
            fail(f"template_version {tv} < TEMPLATE_VERSION {skeleton.template_version()} (run migrate.py)")

    for rel in skeleton.ROOT_REQUIRED:
        if not (prod / rel).is_file():
            fail(f"required file missing: {rel}")
    unit_list = skeleton.units(prod, fmt)
    if not unit_list:
        fail("no unit folder (show needs 'S01E01 - <name>/')")
    for u in unit_list:
        for rel in skeleton.UNIT_REQUIRED:
            if not (u / rel).is_file():
                fail(f"required file missing: {u.relative_to(prod) if u != prod else '.'}/{rel}")

    for rel in skeleton.walk(prod):
        if rel.suffix == ".py" and rel.name != "identity.py":
            fail(f"code in a production: {rel}")
        elif not skeleton.allowed(prod, fmt, rel):
            fail(f"file not in skeleton: {rel}")

    routed = set(GRAPH_RE.findall((paths.REPO / "routing.md").read_text(encoding="utf-8")))
    for k, g in getattr(ident, "WORKFLOWS", {}).items():
        if g not in routed:
            fail(f"WORKFLOWS[{k!r}] = {g!r} not in routing.md")

    slots = {ent.get("slot") for d in (getattr(ident, "CAST", {}), getattr(ident, "LOCATIONS", {}))
             for ent in d.values() if isinstance(ent.get("slot"), int)}
    pics_ok = {s + 1 for s in slots}
    for u in unit_list:
        for lf in sorted((u / "prompts").glob("*.lines")) if (u / "prompts").is_dir() else []:
            for i, line in enumerate(lf.read_text(encoding="utf-8").splitlines()):
                bad = {int(n) for n in PIC_RE.findall(line)} - pics_ok
                if bad:
                    fail(f"{lf.relative_to(prod)} line {i}: <Picture {sorted(bad)}> not declared in identity slots")

    print(f"measured  {prod.name}: {sum(1 for _ in skeleton.walk(prod))} file(s), {len(unit_list)} unit(s), {faults} fault(s)")
    return 1 if faults else 0


def check_findings() -> int:
    f = paths.REPO / "findings.jsonl"
    bad = 0
    n = 0
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        n += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"DRIFT     findings.jsonl line {n}: not JSON ({e.msg})")
            bad += 1
            continue
        if row.get("count", 0) >= 2 and row.get("status") == "open" \
                and not any(k in row for k in ("check", "fix", "dropped")):
            print(f"DRIFT     finding at count {row['count']} still open: {row['finding'][:80]}")
            bad += 1
    print(f"measured  findings.jsonl: {n} finding(s), {bad} unpromoted at count>=2")
    return 1 if bad else 0


def check_deployed() -> int:
    r = subprocess.run([sys.executable, str(paths.REPO / "workflows" / "deploy.py"), "--check"],
                       capture_output=True, text=True, encoding="utf-8")
    for l in r.stdout.splitlines():
        print(f"deploy    {l}")
    return 1 if r.returncode else 0


def main(argv: list[str]) -> int:
    no_comfy = "--no-comfy" in argv
    argv = [a for a in argv if a != "--no-comfy"]
    rc = 0
    if argv:
        rc |= check_production(skeleton.PRODUCTIONS / argv[0])
    else:
        prods = skeleton.productions()
        for p in prods:
            rc |= check_production(p)
        if not prods:
            print("measured  0 productions")
        rc |= check_findings()
        if not no_comfy:
            rc |= check_deployed()
    print("\nREFUSE: drift detected" if rc else "\nno drift")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
