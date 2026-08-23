Session start for Movie Maker v2. Run, in order, and show the output of each:

1. `git config core.hooksPath hooks` (idempotent) then `python tools/smoke.py`
2. `python tools/drift.py` — if it refuses, fix the drift before anything else (or report it if it is Ronan's to fix)
3. `python tools/status.py` — regenerates STATUS.md; read it
4. `python tools/findings.py check`
5. Read `LAWS.md` once (it is the one long file read every session).

Then tell Ronan, in five lines or fewer: what refused, which production is at which gate, and what the next command is. Do not start any stage without the previous artifact at `status: approved`.
