REFS (G4) for production $ARGUMENTS. One turnaround sheet per character, one EMPTY template per location, optional master wide — all `mm_image_v1` jobs at 1344x768 from `prompts/refs.lines` (see `.claude/skills/reference-sheets/` when it exists; until then: three views, seamless white backdrop, flat even light, feet visible, nothing on the floor).

For every candidate that lands: `python tools/refqc.py <png> --kind sheet --figures 3 --record <slug>` (or `--kind plate --block 40 60`, `--kind crop`). Ronan picks; the pick is copied into `refs/<name>_APPROVED_<seed>.png` (committed), its manifest row set to `status: approved`, and `identity.CAST/LOCATIONS` filled with sheet, seed, slot. Rejects are renamed `*__rej_<reason>.png` on the drive, never deleted.

`python tools/contract.py <slug>` must hold. G4 is every `<Picture N>` the prompts will use backed by an approved sheet.
