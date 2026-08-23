"""residue.py — a new production must not carry another production's identifiers.

  python tools/residue.py <slug>

Measures: beat ids (beats.csv), slot names (slot_names.txt), CAST/LOCATIONS/VOICES
keys and approved-ref filenames of <slug> against every OTHER production.
Refuses on any overlap. Exit 1.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import skeleton  # noqa: E402


def identifiers(prod: Path) -> dict[str, set[str]]:
    ident = skeleton.load_identity(prod)
    out = {
        "cast": set(getattr(ident, "CAST", {})),
        "locations": set(getattr(ident, "LOCATIONS", {})),
        "voices": set(getattr(ident, "VOICES", {})),
        "refs": {p.name for p in (prod / "refs").glob("*_APPROVED_*.png")},
        "beats": set(),
        "slots": set(),
    }
    for unit in skeleton.units(prod, getattr(ident, "FORMAT", "film") or "film"):
        b = unit / "beats.csv"
        if b.is_file():
            with b.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("beat"):
                        out["beats"].add(row["beat"].strip())
        s = unit / "slot_names.txt"
        if s.is_file():
            out["slots"].update(l.strip() for l in s.read_text(encoding="utf-8").splitlines() if l.strip())
    return out


def check(prod: Path) -> int:
    mine = identifiers(prod)
    hits = 0
    others = [p for p in skeleton.productions() if p != prod]
    for other in others:
        theirs = identifiers(other)
        for kind in mine:
            common = mine[kind] & theirs[kind]
            for c in sorted(common):
                print(f"RESIDUE   {kind} {c!r} also in productions/{other.name}")
                hits += 1
    counted = {k: len(v) for k, v in mine.items()}
    print(f"measured  {prod.name}: {counted} against {len(others)} other production(s)")
    if hits:
        print(f"\nREFUSE: {hits} identifier(s) belong to another production")
        return 1
    print("no residue")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(check(skeleton.PRODUCTIONS / sys.argv[1]))
