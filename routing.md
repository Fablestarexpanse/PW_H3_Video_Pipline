# routing — job → graph → settings

One table. `render.py` refuses a job whose `graph` is not in it; `drift.py` refuses a
production that references anything else. Graphs live in `workflows/` and are deployed by
`workflows/deploy.py`; a change is a new version + a row here, old copy to `workflows/archive/`.
Everything that varies per job is a row in `jobs.jsonl`, never a saved graph (spec §7).

| Job | Graph | Model stack | Regime (frozen) | Variable inputs (and nothing else) |
|---|---|---|---|---|
| **Stills** — sheets, location templates, plates, look tests | `mm_image_v1` | Krea-2 int8 `myKrea2UnlockedInt8_v10` · `qwen3vl_4b_fp8_scaled` (type `krea2`) · `Qwen_Image-VAE` | 11 steps · cfg 1.0 · euler/simple · ConditioningZeroOut negative · NegPip via `Krea2PromptWeight` | `line` (index into `prompts/<unit>.lines`) · `negpip` line · `lora` inline string · `seed` · `width`/`height` · `prefix` |
| **Edits** — change one thing on an existing render — **UNPROVEN, not routed** (see findings: base Klein at 4 steps reproduces the source unchanged) | `mm_edit_v1` | Flux-2 Klein **base** 9B fp8 · `qwen_3_8b_fp8mixed` (type `flux2`) · `full_encoder_small_decoder` | 4 steps · cfg 1.0 · euler · Flux2Scheduler · source as reference latent; output size = source size | `source` image · `prompt` (edit text) · `seed` · `prefix` |
| **Clips** — any single H3 generation, 5–15 s | `mm_clip_v1` | H3 `minimax_h3_fl2va_pruned_int8_convrot` · `qwen3vl_32b_minimax_h3_nvfp4_awq` (type `minimax`) · video VAE fp16 · audio VAE fp32 | 20 steps · res_multistep/simple · size from `<Picture 1>` via GetImageSize | `line` · up to 9 `refs` (`ref_image_0..8`) · up to 3 `audio` (`ref_audio_0..2`) · `frames` (17k+5, set directly on `length`) · `seed` · `prefix` |
| **Chain** — long-form ≥ 1 min, or any lip-synced performance to a real track | `mm_chain_v1` | H3 int8 as above but video VAE `minimax_h3_video_vae_int8_convrot` · SageAttention · SolAttn · SigmaShift 12/3 | 20 steps · euler/simple · 960×544 · context 22 · encode `video` · anchor `head` · `audio_mode: source_track` · crf 18 | `plan_json` · `run_name` · `fingerprint` · up to 9 `refs` · `cond_audio` (stem) · `mux_audio` (master) · `base_seed` |

## Sizes
- Anything bound for H3: **1344×768** (H3-native; a sheet prompt saying "exactly three" holds here and not at 3264×1836).
- Krea-2 storyboard 3:2: 1216×832 · portrait 832×1216 · square/identity 1024×1024.
- Clip size is never typed: `mm_clip` reads it from `<Picture 1>`. Chain size is a Plan widget (multiples of 32).

## H3 frame grid (24 fps, 17k+5)
| Frames | 124 | 175 | 226 | 260 | 277 | **294** | **311** | **328** | **345** | **362** |
|---|---|---|---|---|---|---|---|---|---|---|
| Seconds | 5.17 | 7.29 | 9.42 | 10.83 | 11.54 | 12.25 | **12.96** (default beat) | 13.67 | 14.38 | **15.08** (dialogue / title) |

`mm_clip_v1` sets `length` in frames directly (the node enforces `min 5, step 17`), so the old
duration-widget trap (`13.0` → 328 frames) no longer exists on the clip path. It still exists
inside the chain plan (`duration_seconds` rounds **up**); use `length` there for frame-exact.
362 is the edge of the trained range — split the beat or use the chain beyond it.

## Chain arithmetic
Context 22 / anchor head: segment 1 delivers its full length, every later segment delivers
`length − 22`. At 362: `total = 15.083 + (N − 1) × 14.167` s.

## Measured cost (fill `costs.csv`; never extrapolate — superlinear)
| Graph | Job | Measured |
|---|---|---|
| Krea-2 | 1344×768, 8–11 steps, 3 LoRAs | ~75–90 s |
| H3 clip | 124 f | 11.9 s/step → ~4 min sampling; cold load ~3.5 min · **v2 measured 2026-08-23: 4.98 min wall at 1344×768, 1 ref (`costs.csv`)** |
| H3 clip | 226 f | 31.8 s/step → ~10.6 min |
| H3 clip | 362 f @ 1152×640 (WTTB) | 13–15 min wall |
| Chain | 20-step, 362 f segments | **unmeasured** — measure on segment 1 before quoting |
| Klein edit | 1344×768, base 9B, 4 steps | 18.9 min right after an H3 clip (VRAM contention suspected) — and it did not edit; unproven |

## Levers that work, per model
- **Krea-2**: prompt negatives do nothing at cfg 1.0. NegPip `(word:-1.2…-1.5)` works, for standing
  style-stack taxes only; don't push past −1.8 (backs go hollow). Width beats the word "three".
  The LoRA stack is inline `<lora:name:w>` syntax — the LoraManager stackers cannot be driven
  headless (`AUTOCOMPLETE_TEXT_LORAS` is frontend-only). A style LoRA's trigger word is prepended by
  Trigger Word Toggle (untested off). The graph ships with NO stack: `identity.STYLE_STACK` is applied per job.
- **Klein**: cannot carry Krea-2 LoRAs — look comes from the source image. Name only the change.
- **H3**: negatives work only as positive statements of the mode (see `LAWS.md` §4). `<Picture N>`
  numbering follows slot index; unused slots are **bypassed** by `render.py` (proven: a bypassed
  `LoadImage` vanishes from the API prompt and its slot is dropped from the H3 node).

## Retired / not routed
Everything in ComfyUI `workflows/archive/` (95 graphs, moved 2026-08-22, not deleted). No
`api_*` templates, no `partner/` nodes, ever. Turbo LoRA (`lightx2v_turbo_4step`) and
`MiniMaxH3MemoryEfficientSageAttentionPatch` dropped from the chain graph — the first unproven on
int8, the second not installed. Each is a named upgrade with its own proof clip if ever wanted.
