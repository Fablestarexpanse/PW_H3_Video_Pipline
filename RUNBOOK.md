# RUNBOOK — host facts and what only Ronan does by hand

Written as facts are discovered, not at the end.

## Host
- Windows 11, RTX 4090. Python 3.11.9 at `C:\Program Files\Python311`.
- ffmpeg/ffprobe 8.1 (winget Gyan build) on PATH.
- ComfyUI: `F:\Stability Matrix\Packages\ComfyUI`; saved workflows in `user\default\workflows` (96 files on 2026-08-22, to be archived in step 2).
- Media root `F:\MovieMaker` — created by `tools/paths.py` on 2026-08-22.
- Repo: `F:\Cursor Projects\PW_H3_Video_Pipline` → https://github.com/Fablestarexpanse/PW_H3_Video_Pipline

## Source material (read-only)
- Old vault: `C:\Users\Brian\Documents\Feyndral\Movie Maker` (`00 System`, `01 Templates`, `Productions`). Never write to it.
- Old tools: `F:\stems\moviemaker_tools\` (`clipqc.py`, `make_tagged.py`).

## comfy-draftsman facts (2026-08-22, ComfyUI v0.33.1)
- `import_workflow(name=...)` reads `user\default\workflows\<name>.json`; subfolders appear as `archive/<name>`.
- `save_workflow` is blocked by the Claude Code permission classifier in this environment. Not needed: the repo
  JSON is the source, `workflows/deploy.py` copies it in. Never save from a run anyway (spec §7b).
- `set_widget` on `LoadImage.image` / `LoadAudio.audio` refuses files not in the node's cached choice list even
  when the file is in `input/`; pass `force: true`. `validate_workflow` then passes.
- **Bypass (mode 4) on a `LoadImage`/`LoadAudio` removes it and its `ref_image_N`/`ref_audio_N` slot from the API
  prompt entirely** — confirmed with `export_workflow_json(format="api")`. This is how `render.py` leaves unused
  ref slots out of conditioning without rewiring.
- `MiniMaxH3ReferenceToVideo.length` is a plain INT widget, `min 5, step 17` → frames go in directly.
- Models actually installed: Klein is **`flux-2-klein-base-9b-fp8`** only (no distilled file). H3 video VAE exists
  as both `fp16` and `int8_convrot`; audio VAE at `h3\minimax_h3_audio_vae_fp32` and root.
- `MiniMaxH3MemoryEfficientSageAttentionPatch` is not installed (LTX2/Wan variants are).
- Subgraph-instance workflows (the Klein edit template) cannot be widget-driven with plain `set_widget`; the
  frozen `mm_edit_v1` is a flat rebuild of the single-input instance.
- Windows console is cp1252: every tool does `sys.stdout.reconfigure(encoding="utf-8")` first thing, or a
  workflow name with `—`/`ō` crashes the print.

## What only Ronan does by hand
- Approve: flip `status:` in a file and commit.
- Install custom node packs (third-party code) — never done by the pipeline.
- Un-mute the two amber recovery nodes in `mm_chain` and mute the main Assemble to rebuild from checkpoints.

## Git hooks
- Hooks are tracked in `hooks/` and enabled with `git config core.hooksPath hooks` (run once per clone; also
  done by `/start`). `pre-commit` runs `tools/smoke.py` then `tools/drift.py` (which calls `deploy.py --check`,
  so ComfyUI must be reachable — use `drift.py --no-comfy` manually if it is down, never skip the hook).

## ComfyUI HTTP API (what render.py / landed.py use)
- `POST http://127.0.0.1:8188/prompt` with `{"prompt": <api-format graph>, "client_id": "moviemaker-v2"}` → `{"prompt_id"}`;
  a bad graph returns 400 with `node_errors`. `GET /history/<prompt_id>` → `{pid: {outputs: {node: {images: [{filename, subfolder, type}]}}, status: {status_str, completed, messages}}}`;
  absent until the job finishes. `GET /queue` → `queue_running` / `queue_pending` lists of `[number, prompt_id, ...]`.
- Outputs land under `output/<filename_prefix>…_00001_.png|mp4`; chain runs write `output/h3_chain/<run_name>/`.
- `landed.py` measured: a 512×512 Krea-2 still queued → landed in ~25 s wall on a warm instance.

## Assembly facts (2026-08-23)
- Segments video-only; audio as PCM wav per segment, concat, mux once with `atrim` → audio duration == picture to the sample (AAC priming is declared in the edit list; ffprobe reads 38.875000 for 933 frames).
- Always decode with `-fps_mode passthrough` when counting or sampling frames; CFR mode duplicates across a concat seam with an edit-list offset.
- Tag font: `C:/Windows/Fonts/consola.ttf` (pass `--font` for another). ffmpeg drawtext wants the colon escaped: `C\:/Windows/...`.
- A 3-slot 933-frame cut: assemble ~20 s, cutqc ~6 s, tag (854 tagged + 720 web) ~25 s.
