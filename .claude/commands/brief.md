BRIEF (G1) for production $ARGUMENTS. One page, five decisions: runtime (s), aspect, audio source, cast count, one-off vs format. Fill the table in `brief.md` and the premise.

If audio is a track: copy it into `productions/<slug>/audio/` (drive-mirrored), measure it with ffprobe, and write `identity.AUDIO` with the MEASURED duration (contract.py refuses a typed one). Run `python tools/contract.py <slug>`.

G1 is Ronan setting `status: approved` in `brief.md`. Refuse to write canon while any of the five is blank.
