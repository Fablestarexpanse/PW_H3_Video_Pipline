"""preflight.py — refuse a prompt line before it costs a render (LAWS.md; spec §3).

  python tools/preflight.py <slug> <unit-or-.> <file.lines> [--line N] [--max-blocks 8]
  python tools/preflight.py --text <file.txt>            one unescaped prompt, no identity
  python tools/preflight.py --selftest                   calibration/prompts/{good,bad}

Measures the EXACT line the graph will load (CUN_TextFileLineLoader: utf-8, stripped,
blank lines skipped; JWStringUnescape: ascii/backslashreplace -> unicode-escape).

Refuses (exit 1) on:
  discretion   a "not shown" clause — LAWS §3      stale_neg    a bare negative list — LAWS §4
  scale_state  a SCALE STATE block — LAWS §2       frame_zero   retention_analysis has no frame-zero description — LAWS §1/§8
  blocks       more named blocks than the template allows — LAWS §10
  sections     Ref2VA sections missing / out of order (h3-prompt-writing)
  unapproved   <Picture N> not backed by an *_APPROVED_* sheet in identity — LAWS §8
  roundtrip    line is not byte-stable through strip + unescape + re-escape
  blank_line   a blank line in the .lines file (shifts every later index)
Advisory (printed, never refuses):
  lock_thrice  a camera lock stated in fewer than three sections — LAWS §11
  negation     every single 'no / never / without' for the decision LAWS §1 asks for
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paths  # noqa: E402

DISCRETION = ("never shown", "out of view", "hidden", "not visible", "off-screen", "offscreen",
              "implied", "we do not see", "we don't see", "is not shown", "isn't shown", "unseen")
SECTIONS = ("subject_definitions", "summary", "retention_analysis", "detailed_description",
            "overall_soundscape", "non_diegetic_music")
FRAME_ZERO = re.compile(r"\b(first frame|frame zero|frame 0|opening frame|00:00[.:]000|opens on|at 0\.0+\s*s)\b", re.I)
PIC_RE = re.compile(r"<Picture (\d+)>")
BARE_NEG = re.compile(r"\b(?:no|without)\s+(?:[a-z-]+\s){0,3}[a-z-]+", re.I)
NEG_WORD = re.compile(r"\b(no|never|without|not)\b", re.I)
# A named rule block: "MOUTH STATE:", "CAMERA LOCK:", "WEAPON RULE:", "READ THIS FIRST:" — uppercase label + colon.
BLOCK_RE = re.compile(r"\b([A-Z][A-Z-]+(?: [A-Z][A-Z-]+){0,4}(?: STATE| RULE| LOCK| WINDOW| BUDGET| FIRST| ONLY))\s*:")
LOCK_RE = re.compile(r"\b(locked(?:-off)?|lock(?:ed)? (?:camera|off)|camera (?:is|stays|remains) (?:locked|static|fixed)|does not move|never moves)\b", re.I)
DEFAULT_MAX_BLOCKS = 16   # the Ref2VA Clip Prompt Template defines 16 named STATE blocks (LAWS §10)
FIXTURES = paths.REPO / "calibration" / "prompts"


def jw_unescape(text: str) -> str:
    r"""Exactly what JWStringUnescape does — but an invalid escape (\s, \q) is a refusal here,
    where on the instance it is a DeprecationWarning and the prompt silently renders changed."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return text.encode("ascii", "backslashreplace").decode("unicode-escape")


def escape(text: str) -> str:
    """The inverse the .lines author must use: one prompt → one line."""
    return text.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "")


def sections_of(text: str) -> dict[str, str]:
    """Split a Ref2VA prompt on its section labels; {} if not Ref2VA-shaped."""
    pos = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^(%s)\s*:" % "|".join(SECTIONS), text)]
    if not pos:
        return {}
    out = {}
    for i, (start, name) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        out[name] = text[start:end]
    return out


class Result:
    def __init__(self, label: str):
        self.label = label
        self.refusals: list[tuple[str, str]] = []
        self.advisories: list[tuple[str, str]] = []

    def refuse(self, code: str, msg: str) -> None:
        self.refusals.append((code, msg))

    def advise(self, code: str, msg: str) -> None:
        self.advisories.append((code, msg))

    def report(self) -> int:
        for c, m in self.advisories:
            print(f"advise    {self.label} [{c}] {m}")
        for c, m in self.refusals:
            print(f"REFUSE    {self.label} [{c}] {m}")
        return 1 if self.refusals else 0


def check_prompt(text: str, label: str, approved_pics: set[int] | None, max_blocks: int) -> Result:
    r = Result(label)
    low = text.lower()

    for phrase in DISCRETION:
        for m in re.finditer(re.escape(phrase), low):
            ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
            r.refuse("discretion", f"{phrase!r}: …{ctx}…")

    if "scale state" in low:
        r.refuse("scale_state", "SCALE STATE block present — delete it; carry scale above and behind the subject")

    for sent in re.split(r"(?<=[.;!?\n])\s+", text):
        bare = BARE_NEG.findall(sent)
        if len(bare) >= 2 or re.search(r"(?i)\bnegative(?: prompt)?\s*:", sent):
            r.refuse("stale_neg", f"negative list: {sent.strip()[:100]!r}")
    negs = [m.group(0) for m in NEG_WORD.finditer(text)]
    if negs:
        r.advise("negation", f"{len(negs)} negation word(s): " + ", ".join(
            text[max(0, m.start() - 12): m.end() + 24].replace("\n", " ").strip() for m in list(NEG_WORD.finditer(text))[:6]))

    secs = sections_of(text)
    if secs:
        order = [s for s in SECTIONS if s in secs]
        found = list(secs)
        if found != order:
            r.refuse("sections", f"section order {found} != {order}")
        for must in ("subject_definitions", "summary", "retention_analysis", "detailed_description"):
            if must not in secs:
                r.refuse("sections", f"missing section {must}")
        if "retention_analysis" in secs and not FRAME_ZERO.search(secs["retention_analysis"]):
            r.refuse("frame_zero", "retention_analysis does not describe frame zero positively (LAWS §1: the reference plate gets reproduced, corr +0.97)")
        if LOCK_RE.search(text):
            where = [s for s in ("summary", "retention_analysis", "detailed_description") if s in secs and LOCK_RE.search(secs[s])]
            if len(where) < 3:
                r.advise("lock_thrice", f"camera lock stated in {where} — LAWS §11 wants summary + retention_analysis + shot description")

    blocks = sorted(set(BLOCK_RE.findall(text)))
    if len(blocks) > max_blocks:
        r.refuse("blocks", f"{len(blocks)} named blocks > {max_blocks}: {blocks} — cut a rule before adding one (LAWS §10)")

    pics = {int(n) for n in PIC_RE.findall(text)}
    if approved_pics is not None:
        bad = sorted(pics - approved_pics)
        if bad:
            r.refuse("unapproved", f"<Picture {bad}> not backed by an approved sheet in identity (approved: {sorted(approved_pics)})")
    return r


def check_line_file(lf: Path, approved_pics: set[int] | None, max_blocks: int, only: int | None) -> int:
    raw = lf.read_text(encoding="utf-8")
    rc = 0
    physical = raw.split("\n")
    if physical and physical[-1] == "":
        physical = physical[:-1]
    for i, line in enumerate(physical):
        if not line.strip():
            print(f"REFUSE    {lf.name}:{i} [blank_line] blank line — the loader skips it and every later index shifts")
            rc = 1
    logical = [l for l in physical if l.strip()]
    for idx, line in enumerate(logical):
        if only is not None and idx != only:
            continue
        label = f"{lf.name}[{idx}]"
        r = Result(label)
        stripped = line.strip()
        if stripped != line:
            r.refuse("roundtrip", "leading/trailing whitespace — the loader strips it, so the file is not what renders")
        try:
            text = jw_unescape(stripped)
        except (UnicodeDecodeError, DeprecationWarning) as e:
            r.refuse("roundtrip", f"unescape fails: {e}")
            rc |= r.report()
            continue
        if escape(text) != stripped:
            r.refuse("roundtrip", "escape(unescape(line)) != line — a stray backslash or \\r is changing the prompt")
        rc |= r.report()
        pr = check_prompt(text, label, approved_pics, max_blocks)
        rc |= pr.report()
        print(f"measured  {label}: {len(text)} chars, {len(sections_of(text))} sections, {len(set(BLOCK_RE.findall(text)))} blocks, pics {sorted({int(n) for n in PIC_RE.findall(text)})}")
    return rc


def approved_from_identity(slug: str) -> set[int]:
    import skeleton
    prod = skeleton.PRODUCTIONS / slug
    ident = skeleton.load_identity(prod)
    ok = set()
    for d in (ident.CAST, ident.LOCATIONS):
        for key, ent in d.items():
            sheet = prod / ent.get("sheet", "")
            if sheet.is_file() and "_APPROVED_" in sheet.name and isinstance(ent.get("slot"), int):
                ok.add(ent["slot"] + 1)
    return ok


def selftest() -> int:
    good = sorted((FIXTURES / "good").glob("*.txt"))
    bad = sorted((FIXTURES / "bad").glob("*.txt"))
    if not good or not bad:
        print(f"REFUSE: need fixtures in {FIXTURES}/good and /bad")
        return 1
    fails = 0
    for f in good:
        r = check_prompt(f.read_text(encoding="utf-8"), f.stem, {1, 2, 3}, DEFAULT_MAX_BLOCKS)
        if r.refusals:
            fails += 1
            print(f"FAIL      good/{f.name} refused: {[c for c, _ in r.refusals]}")
        else:
            print(f"ok        good/{f.name} passes")
    for f in bad:
        expect = f.stem.split("__")[0]
        r = check_prompt(f.read_text(encoding="utf-8"), f.stem, {1, 2, 3}, DEFAULT_MAX_BLOCKS)
        codes = [c for c, _ in r.refusals]
        if expect not in codes:
            fails += 1
            print(f"FAIL      bad/{f.name} expected [{expect}], got {codes}")
        else:
            print(f"ok        bad/{f.name} refused [{expect}]")
    # line-file mechanics
    tmp = FIXTURES / "_roundtrip.lines"
    tmp.write_text("a line\n\n  padded \nback\\slash\\q\n", encoding="utf-8")
    rc = check_line_file(tmp, None, DEFAULT_MAX_BLOCKS, None)
    tmp.unlink()
    if rc != 1:
        fails += 1
        print("FAIL      line-file mechanics did not refuse blank/padded/unescapable lines")
    else:
        print("ok        line-file mechanics refuse blank / padded / unescapable lines")
    print(f"\n{'REFUSE: ' + str(fails) + ' selftest failure(s)' if fails else f'selftest passes: {len(good)} good, {len(bad)} bad, mechanics'}")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("pos", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--text")
    ap.add_argument("--line", type=int)
    ap.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.text:
        r = check_prompt(Path(a.text).read_text(encoding="utf-8"), Path(a.text).name, None, a.max_blocks)
        rc = r.report()
        print("\nREFUSE" if rc else "\npreflight passes")
        return rc
    if len(a.pos) != 3:
        print(__doc__)
        return 1
    slug, unit, lines = a.pos
    import skeleton
    prod = skeleton.PRODUCTIONS / slug
    lf = (prod if unit == "." else prod / unit) / "prompts" / lines
    if not lf.is_file():
        print(f"REFUSE: {lf} not found")
        return 1
    rc = check_line_file(lf, approved_from_identity(slug), a.max_blocks, a.line)
    print("\nREFUSE: preflight" if rc else "\npreflight passes")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
