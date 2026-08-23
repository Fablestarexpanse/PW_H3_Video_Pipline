PROOF (G5) for production $ARGUMENTS: one clip, the hardest beat, at the SHIPPED length.

Add one `mm_clip_v1` row to `jobs.jsonl` (id `<beat>_s<seed>`, `frames` from beats.csv, `refs` slot->file, `seed` fixed). Queue `python tools/render.py <slug> <unit|.> <id>` (`--proof` is allowed once per production if refs are still candidates), land with `landed.py --watch`, then `python tools/clipqc.py <clip> --ref <location plate> --frames N` and look at the filmstrip. `python tools/costs.py ingest <slug>` writes the measured minutes; `costs.py quote --graph mm_clip_v1 --frames N` must answer before the board is quoted.

G5 is Ronan confirming identity on the proof. No board before G5.
