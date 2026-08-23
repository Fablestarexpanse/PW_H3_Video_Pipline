"""migrate.py — bring every production up to templates/TEMPLATE_VERSION.

  python tools/migrate.py            migrate all
  python tools/migrate.py <slug>     migrate one

Adds any required file the production lacks (copied from templates/production/),
adds any identity.py field the template declares that the production lacks
(appended with the template's default), then writes template_version.
Never deletes or rewrites existing content. Refuses on an identity.py field the
template does NOT declare — that is drift a human must resolve. Exit 1 on refusal.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import skeleton  # noqa: E402


def template_default(field: str) -> str:
    src = (skeleton.TEMPLATE_DIR / "identity.py").read_text(encoding="utf-8")
    m = re.search(rf"^{field} = .*?$(?:\n(?!\w).*?$)*", src, re.M)
    if not m:
        raise SystemExit(f"REFUSE: template identity.py has no default for {field}")
    return m.group(0)


def migrate(prod: Path) -> int:
    changed = 0
    ident = skeleton.load_identity(prod)
    fmt = getattr(ident, "FORMAT", "film") or "film"
    declared = {k for k in vars(ident) if k.isupper()}
    extra = sorted(declared - set(skeleton.IDENTITY_FIELDS))
    if extra:
        print(f"REFUSE: {prod.name}/identity.py declares {extra}, which the template does not")
        return 1
    missing = [f for f in skeleton.IDENTITY_FIELDS if f not in declared]
    if missing:
        with (prod / "identity.py").open("a", encoding="utf-8") as fh:
            for f in missing:
                fh.write("\n" + template_default(f) + "\n")
                print(f"added     {prod.name}/identity.py: {f}")
                changed += 1
    for rel in skeleton.ROOT_REQUIRED:
        if rel == "template_version":
            continue
        if not (prod / rel).is_file():
            (prod / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(skeleton.TEMPLATE_DIR / rel, prod / rel)
            print(f"added     {prod.name}/{rel}")
            changed += 1
    for u in skeleton.units(prod, fmt):
        for rel in skeleton.UNIT_REQUIRED:
            if not (u / rel).is_file():
                (u / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(skeleton.TEMPLATE_DIR / "_unit" / rel, u / rel)
                print(f"added     {prod.name}/{u.relative_to(prod) if u != prod else '.'}/{rel}")
                changed += 1
        (u / "prompts").mkdir(exist_ok=True)
    tv = skeleton.template_version()
    cur = (prod / "template_version").read_text(encoding="utf-8").strip() if (prod / "template_version").is_file() else "none"
    (prod / "template_version").write_text(f"{tv}\n", encoding="utf-8")
    print(f"migrated  {prod.name}: template_version {cur} -> {tv}, {changed} file(s)/field(s) added")
    return 0


def main(argv: list[str]) -> int:
    prods = [skeleton.PRODUCTIONS / argv[0]] if argv else skeleton.productions()
    if not prods:
        print("no productions")
        return 0
    return max(migrate(p) for p in prods)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
