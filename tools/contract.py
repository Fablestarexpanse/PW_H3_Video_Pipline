"""contract.py — one fact, one file, cross-checked (spec §0.3, §2).

  python tools/contract.py <slug>          check one production
  python tools/contract.py --all           check every production

Refuses (exit 1) when two files disagree. Prints every measurement.

Facts checked
  identity.TITLE non-blank · FORMAT film|show · every identity field declared
  WORKFLOWS values are graphs named in routing.md
  every CAST/LOCATIONS sheet exists, is *_APPROVED_<seed>.png with the SAME seed, and is in refs/manifest.json
  no two CAST/LOCATIONS entries share a slot
  beats.csv: frames on 17k+5 · every ref key is a canon file (characters/ or locations/) or an identity key · cut_time monotonic
  slot_names.txt line count == beats.csv row count
  prompts/<unit>.lines: line count == beat count · every <Picture N> ⊆ declared slots+1 ·
                        any line with (S<n>) carries a VOICES phrase byte-identical
  AUDIO.duration == ffprobe(master) to 5 ms, stem duration == master
"""
from __future__ import annotations

import csv
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
SPK_RE = re.compile(r"\(S\d\)")
GRAPH_RE = re.compile(r"`(mm_(?:image|edit|clip|chain)_v\d+)`")


def routed_graphs() -> set[str]:
    return set(GRAPH_RE.findall((paths.REPO / "routing.md").read_text(encoding="utf-8")))


def on_grid(frames: int) -> bool:
    return frames >= 5 and (frames - 5) % 17 == 0


def ffprobe_duration(p: Path) -> float:
    out = subprocess.run(
        [str(paths.FFPROBE), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


class Contract:
    def __init__(self, prod: Path):
        self.prod = prod
        self.faults: list[str] = []

    def fail(self, msg: str) -> None:
        self.faults.append(msg)
        print(f"DISAGREE  {msg}")

    def ok(self, msg: str) -> None:
        print(f"ok        {msg}")

    def run(self) -> int:
        prod = self.prod
        ident = skeleton.load_identity(prod)
        for f in skeleton.IDENTITY_FIELDS:
            if not hasattr(ident, f):
                self.fail(f"identity.py lacks {f}")
        if self.faults:
            return self.verdict()

        if not ident.TITLE.strip():
            self.fail("identity.TITLE is blank")
        if ident.FORMAT not in ("film", "show"):
            self.fail(f"identity.FORMAT = {ident.FORMAT!r}, must be film|show")
        routed = routed_graphs()
        for k, g in ident.WORKFLOWS.items():
            if g not in routed:
                self.fail(f"identity.WORKFLOWS[{k!r}] = {g!r} is not in routing.md")
        self.ok(f"WORKFLOWS {sorted(ident.WORKFLOWS.values())} all in routing.md") if not self.faults else None

        manifest = json.loads((prod / "refs" / "manifest.json").read_text(encoding="utf-8"))
        manifest_files = {r.get("file") for r in manifest.get("refs", [])}
        slots: dict[int, str] = {}
        for kind in ("CAST", "LOCATIONS"):
            for key, ent in getattr(ident, kind).items():
                sheet, seed, slot = ent.get("sheet"), ent.get("seed"), ent.get("slot")
                if not isinstance(slot, int):
                    self.fail(f"{kind}[{key!r}].slot missing")
                    continue
                if slot in slots:
                    self.fail(f"{kind}[{key!r}].slot {slot} also used by {slots[slot]!r}")
                slots[slot] = key
                p = prod / sheet if sheet else None
                if not p or not p.is_file():
                    self.fail(f"{kind}[{key!r}].sheet {sheet!r} does not exist")
                    continue
                m = re.search(r"_APPROVED_(\d+)\.png$", p.name)
                if not m:
                    self.fail(f"{kind}[{key!r}].sheet {p.name} is not *_APPROVED_<seed>.png")
                elif int(m.group(1)) != seed:
                    self.fail(f"{kind}[{key!r}].seed {seed} != filename seed {m.group(1)}")
                if p.name not in manifest_files:
                    self.fail(f"{kind}[{key!r}].sheet {p.name} not in refs/manifest.json")
        self.ok(f"{len(slots)} reference slot(s): " + ", ".join(f"<Picture {s+1}>={k}" for s, k in sorted(slots.items())))
        # G3: a beat ref is a CANON key (characters/<key>.md or locations/<key>.md). The approved sheet
        # behind it is G4's business (identity CAST/LOCATIONS; preflight/render refuse an unapproved <Picture N>).
        ref_keys = {p.stem for d in ("characters", "locations") for p in (prod / d).glob("*.md") if p.name != "_TEMPLATE.md"}
        ref_keys |= set(ident.CAST) | set(ident.LOCATIONS)
        declared_pics = {s + 1 for s in slots}

        for unit in skeleton.units(prod, ident.FORMAT if ident.FORMAT in ("film", "show") else "film"):
            self.check_unit(unit, ident, ref_keys, declared_pics)

        if ident.AUDIO:
            self.check_audio(ident.AUDIO)
        else:
            self.ok("AUDIO empty (no external track)")
        return self.verdict()

    def check_unit(self, unit: Path, ident, ref_keys: set[str], declared_pics: set[int]) -> None:
        name = unit.name if unit != self.prod else "(film root)"
        beats: list[dict] = []
        with (unit / "beats.csv").open(encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            if rd.fieldnames != ["beat", "frames", "mode", "refs", "state_changes", "cut_time"]:
                self.fail(f"{name}/beats.csv header {rd.fieldnames} != beat,frames,mode,refs,state_changes,cut_time")
                return
            beats = [r for r in rd if any(v.strip() for v in r.values())]
        total = 0
        last_cut = -1.0
        for i, b in enumerate(beats):
            try:
                fr = int(b["frames"])
            except ValueError:
                self.fail(f"{name} beat {b['beat']!r}: frames {b['frames']!r} not an int")
                continue
            if not on_grid(fr):
                self.fail(f"{name} beat {b['beat']!r}: {fr} frames not on 17k+5")
            total += fr
            for r in filter(None, (x.strip() for x in b["refs"].split(";"))):
                if r not in ref_keys:
                    self.fail(f"{name} beat {b['beat']!r}: ref {r!r} is not a canon key (characters/ or locations/) or identity key")
            if b["cut_time"].strip():
                ct = float(b["cut_time"])
                if ct <= last_cut:
                    self.fail(f"{name} beat {b['beat']!r}: cut_time {ct} not after previous {last_cut}")
                last_cut = ct
        self.ok(f"{name}: {len(beats)} beat(s), {total} frames = {total/24:.3f} s")

        slot_lines = [l for l in (unit / "slot_names.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(slot_lines) != len(beats):
            self.fail(f"{name}: slot_names.txt has {len(slot_lines)} names, beats.csv has {len(beats)} beats")
        else:
            self.ok(f"{name}: slot_names.txt count {len(slot_lines)} == beat count")

        voices = list(ident.VOICES.values())
        ASSET_FILES = {"refs.lines", "looktest.lines"}  # per-asset, not per-beat
        for lf in sorted((unit / "prompts").glob("*.lines")):
            lines = lf.read_text(encoding="utf-8").split("\n")
            if lines and lines[-1] == "":
                lines = lines[:-1]
            if beats and lf.name not in ASSET_FILES and len(lines) != len(beats):
                self.fail(f"{name}/prompts/{lf.name}: {len(lines)} line(s) != {len(beats)} beat(s)")
            for i, line in enumerate(lines):
                pics = {int(n) for n in PIC_RE.findall(line)}
                bad = pics - declared_pics
                if bad:
                    self.fail(f"{name}/prompts/{lf.name} line {i}: <Picture {sorted(bad)}> not a declared slot")
                if SPK_RE.search(line) and not any(v and v in line for v in voices):
                    self.fail(f"{name}/prompts/{lf.name} line {i}: has a speaker tag but no byte-identical VOICES phrase")
            self.ok(f"{name}/prompts/{lf.name}: {len(lines)} line(s) checked")

        self.check_landed_files(unit, name)

    def check_landed_files(self, unit: Path, name: str) -> None:
        # jobs.jsonl says a job "landed" and names its output files; assemble.py trusts that name
        # blindly. A copy-vs-record mismatch here is invisible until someone runs assemble.py on
        # the finished board (measured 2026-08-23: landed.py recorded the pre-copy filename while
        # every actual file on disk carried a "<job_id>__" prefix — every beat silently pointed at
        # a file that never existed). Check it the moment a job lands, not at the end of the board.
        jobs_path = unit / "jobs.jsonl"
        if not jobs_path.is_file():
            return
        slug = self.prod.name
        unit_name = unit.name if unit != self.prod else None
        candidates = [
            paths.media_for(slug, *([unit_name] if unit_name else []), "clips"),
            paths.media_for(slug, "refs", "candidates"),
        ]
        checked = missing = 0
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") != "landed":
                continue
            for fname in row.get("landed_files") or []:
                checked += 1
                if not any((d / fname).is_file() for d in candidates):
                    missing += 1
                    self.fail(f"{name}/jobs.jsonl {row['id']}: landed_files entry {fname!r} not found in clips/ or refs/candidates/")
        if checked and not missing:
            self.ok(f"{name}/jobs.jsonl: {checked} landed_files entr{'y' if checked == 1 else 'ies'} all present on disk")

    def check_audio(self, audio: dict) -> None:
        master = self.prod / audio.get("master", "")
        if not master.is_file():
            self.fail(f"AUDIO.master {audio.get('master')!r} does not exist")
            return
        measured = ffprobe_duration(master)
        declared = float(audio.get("duration", -1))
        if abs(measured - declared) > 0.005:
            self.fail(f"AUDIO.duration {declared} != ffprobe {measured:.3f} (master)")
        else:
            self.ok(f"AUDIO.duration {declared} == ffprobe {measured:.3f}")
        if audio.get("stem"):
            stem = self.prod / audio["stem"]
            if not stem.is_file():
                self.fail(f"AUDIO.stem {audio['stem']!r} does not exist")
            else:
                sd = ffprobe_duration(stem)
                if abs(sd - measured) > 0.005:
                    self.fail(f"AUDIO.stem duration {sd:.3f} != master {measured:.3f}")
                else:
                    self.ok(f"stem duration {sd:.3f} == master")

    def verdict(self) -> int:
        if self.faults:
            print(f"\nREFUSE: {len(self.faults)} disagreement(s) in productions/{self.prod.name}")
            return 1
        print(f"\ncontract holds for productions/{self.prod.name}")
        return 0


def main(argv: list[str]) -> int:
    if argv == ["--all"]:
        prods = skeleton.productions()
        if not prods:
            print("no productions")
            return 0
        return max(Contract(p).run() for p in prods)
    if len(argv) == 1:
        p = skeleton.PRODUCTIONS / argv[0]
        if not (p / "identity.py").is_file():
            print(f"REFUSE: {p} has no identity.py")
            return 1
        return Contract(p).run()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
