"""smoke.py — every module in tools/ and workflows/ imports in a fresh subprocess.

  python tools/smoke.py

Runs at session start and in the pre-commit hook. Refuses (exit 1) on any import
failure, and prints the traceback of each.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    mods = sorted(REPO.glob("tools/*.py")) + sorted(REPO.glob("workflows/*.py"))
    bad = 0
    for m in mods:
        code = f"import sys; sys.path.insert(0, {str(REPO / 'tools')!r}); import importlib.util as u; " \
               f"s=u.spec_from_file_location({m.stem!r}, {str(m)!r}); mod=u.module_from_spec(s); s.loader.exec_module(mod)"
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            bad += 1
            print(f"FAIL      {m.relative_to(REPO)}\n{r.stderr.strip()}")
        else:
            print(f"ok        {m.relative_to(REPO)}")
    print(f"\n{'REFUSE: ' + str(bad) + ' module(s) fail to import' if bad else f'all {len(mods)} modules import'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
