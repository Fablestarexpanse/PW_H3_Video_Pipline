# routing — job → graph → settings

One table. `render.py` refuses a job whose `graph` is not in it; `drift.py` refuses a
production that references anything else. Graphs live in `workflows/` and are deployed by
`workflows/deploy.py`; a change is a new version + a row here, old copy to `workflows/archive/`.
Everything that varies per job is a row in `jobs.jsonl`, never a saved graph (spec §7).

| Job | Graph | Model stack | Regime (frozen) | Variable inputs (and nothing else) |
|---|---|---|---|---|
| **Stills** — sheets, location templates, plates, look tests | `mm_image_v1` | Krea-2 int8 `myKrea2UnlockedInt8_v10` · `qwen3vl_4b_fp8_scaled` (type `krea2`) · `Qwen_Image-VAE` | 11 steps · cfg 1.0 · euler/simple · ConditioningZeroOut negative · NegPip via `Krea2PromptWeight` | `line` (index into `prompts/<unit>.lines`) · `negpip` line · `lora` inline string · `seed` · `width`/`height` · `prefix` |
| **Edits** — change one thing on an existing render — **UNPROVEN, not routed** (see findings: base Klein at 4 steps reproduces the source unchanged) | `mm_edit_v1` | Flux-2 Klein **base** 9B fp8 · `qwen_3_8b_fp8mixed` (type `flux2`) · `full_encoder_small_decoder` | 4 steps · cfg 1.0 · euler · Flux2Scheduler · source as reference latent; output size = source size | `source` image · `prompt` (edit text) · `seed` · `prefix` |
| **Clips** — any single H3 generation, 5–15 s | `mm_clip_v1` | H3 `minimax_h3_fl2va_pruned_int8_convrot` · `qwen3vl_32b_minimax_h3_nvfp4_awq` (type `minimax`) · video VAE fp16 · audio VAE fp32 | 20 steps · res_multistep/simple · fixed 1536×864 (16:9, explicit widget, independent of any ref's own resolution) | `line` · up to 9 `refs` (`ref_image_0..8`) · up to 3 `audio` (`ref_audio_0..2`) · `frames` (17k+5, set directly on `length`) · `seed` · `prefix` |
| **Chain** — long-form ≥ 1 min, or any lip-synced performance to a real track | `mm_chain_v1` | H3 int8 as above but video VAE `minimax_h3_video_vae_int8_convrot` · SageAttention · SolAttn · SigmaShift 12/3 | 20 steps · euler/simple · 1536×864 (16:9) · context 22 · encode `video` · anchor `head` · `audio_mode: source_track` · crf 18 | `plan_json` · `run_name` · `fingerprint` · up to 9 `refs` · `cond_audio` (stem) · `mux_audio` (master) · `base_seed` |
| **Board clips** — a beat pinned between two approved storyboard stills (continuity by construction; the storyboard path) | `mm_ifl_v1` | H3 FL2VA int8 · encoder · VAEs identical to `mm_clip_v1` | 20 steps · res_multistep/simple · size from the FIRST frame via GetImageSize · `MiniMaxH3ImageToVideo` first_frame + last_frame, no reference slots | `line` · `first` (board still N, `*_APPROVED_*`) · `last` (board still N+1, `*_APPROVED_*`) · `frames` (17k+5) · `seed` · `prefix` |

## Lip-sync (mm_chain_v1, audio_mode: source_track)
Before writing any `<d>[English]...</d>` dialogue for a chain job, transcribe the actual cond_audio
slice with whisper (word_timestamps=True) and quote what it measured at that timestamp — never the
written lyric sheet's assumed line order. First real chain test (goose, 2026-08-24): two attempts
with correctly-formatted `<d>` tags still failed because the audio window (0-8.7s, taken naively as
"the opening line") was pure ad-lib vocalization; the real first lyric line didn't start until
9.82s. No tag-format fix could have worked — the model was conditioned on audio that didn't contain
the quoted words at all. `openai-whisper` is installed but only importable from
`C:/Program Files/Python311/python.exe` (the default `python3` on PATH is 3.12 and lacks it). Trim
cond_audio to the exact measured window with `ffmpeg atrim`, one slice per chain job — don't assume
a shot starting at t=0 of the full track covers the intended line.

## The storyboard path (mm_ifl_v1)
Why: with `mm_clip_v1` every beat renders independently from the same plates and sheets, tied to its
neighbours only by prose ("exactly as the previous shot left them") — measured on last_light
(2026-08-24): beats visibly re-stage themselves at every cut. The fix is pixels, not prose:
1. **Board stills** — one `mm_image_v1` still per beat BOUNDARY (n_beats+1 for a film that starts
   and ends on picture), written as `prompts/board.lines` (per-boundary, exempt from the per-beat
   line-count check). Character/location refs and `STYLE_STACK` hold identity. Approved stills are
   copied to `productions/<slug>/boards/<name>_APPROVED_<seed>.png` — same approval naming as refs.
2. **Board clips** — each beat is an `mm_ifl_v1` job: `first` = board still N, `last` = board still
   N+1. The clip opens ON still N and lands ON still N+1; every cut in the film lands on a literally
   shared frame. Clips render in any order (no chain dependency).
3. The prompt for an ifl beat describes the MOTION between the two stills — no `<Picture N>` tags
   (the graph has no reference slots; render.py refuses any that sneak in), no frame-zero
   incantation needed beyond describing the first still as where the clip opens.
Cheap before expensive at its best: the whole film is approved as stills (seconds each) before a
single clip minute is spent.

## Sizes
- Anything bound for H3: **1344×768** (H3-native; a sheet prompt saying "exactly three" holds here and not at 3264×1836).
- Krea-2 storyboard 3:2: 1216×832 · portrait 832×1216 · square/identity 1024×1024.
- `mm_clip_v1` and `mm_chain_v1` are both fixed 1536×864 (16:9, explicit widget on the H3 node, not derived from any ref — refs are conditioning only; fixed 2026-08-24, raised from 1184×672 / 960×544 to exact 16:9 per Ronan). `mm_ifl_v1` is the one graph that still derives size via GetImageSize — from the FIRST board still, which is correct there since board stills are literal pinned frames, not conditioning refs.

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

## LoRA policy (Ronan, 2026-08-23)
**Start with no LoRAs.** A LoRA is added only when it is (a) a speed-up — turbo / lightning / few-step
distillation — or (b) a proven improvement to the workflow itself, each with its own proof render and a
row in `costs.csv`. Character or style LoRAs are never a default; a production that wants one declares
it in `identity.STYLE_STACK` and it rides on that production only. Current state: `mm_image_v1`,
`mm_clip_v1`, `mm_edit_v1` carry no LoRA; `mm_chain_v1`'s turbo LoRA was dropped as unproven on the
int8 model — it is the one candidate under (a), pending a proof segment.

## Levers that work, per model
- **Krea-2**: prompt negatives do nothing at cfg 1.0. NegPip `(word:-1.2…-1.5)` works, for standing
  style-stack taxes only; don't push past −1.8 (backs go hollow). Width beats the word "three".
  The LoRA stack is inline `<lora:name:w>` syntax — the LoraManager stackers cannot be driven
  headless (`AUTOCOMPLETE_TEXT_LORAS` is frontend-only). A style LoRA's trigger word is prepended by
  Trigger Word Toggle (untested off). The graph ships with NO stack: `identity.STYLE_STACK` is applied per job.
- **Klein**: cannot carry Krea-2 LoRAs — look comes from the source image. Name only the change.
- **H3**: negatives work only as positive statements of the mode (see `LAWS.md` §4). `<Picture N>`
  numbering follows slot index; unused slots are **bypassed** by `render.py` (proven: a bypassed
  `LoadImage` vanishes from the API prompt and its slot is dropped from the H3 node). **`ref_image_0`
  (`<Picture 1>`) carries materially more compositional weight than the other 8 slots** — put the
  LOCATION there in any multi-reference clip, never a character: a character at slot 0 produced a
  flat character-sheet lineup with the location ignored; moving the location to slot 0 with identical
  prompt content produced the composited scene (apricot_paper, 2026-08-23).
- **A locked shot at a symmetric architectural plate must state camera asymmetry explicitly**, or
  `ref_leak` climbs beat over beat: a sequence of beats each anchored "exactly as the previous beat
  left them" drifts toward the plate's own centered, head-on composition (apricot_paper gate:
  b02 leak 0.03 → b05 0.42 → b06 0.7–0.9 before a fix). Naming a three-quarter angle that favors one
  side and pushes the plate's centerline off-frame-center dropped it to 0.10 with an unchanged cast
  and location (2026-08-23). Don't leave framing at "medium-wide" defaults on a plate with strong
  bilateral symmetry (an arch, a hearth, a symmetric facade).
- **A near-black night scene needs its practical light source to visibly illuminate the subject, not
  just glow beside them**, or `ref_leak` reads high even with the subject clearly present: at the
  metric's 64x36 decimation a small dark-clothed figure against an already near-black background
  contributes almost no differentiating signal from the empty plate. Seed-only reroll (the fix for a
  genuine leak elsewhere) was unreliable here -- results swung both directions on how much light the
  model happened to render (last_light forest: 0.63→0.95→0.53→0.91 across four seeds, subject visibly
  present in every filmstrip). Double-anchoring "the lantern's light washes onto her face/hands/
  cloak, she reads as warm-lit, never a flat dark silhouette" across subject_definitions,
  retention_analysis AND detailed_description fixed it on the next seed (0.47) (2026-08-23).
- **When a shot's framing shows most of a plate's own architecture, tighten the frame rather than
  just add camera-angle wording** — a locked medium-close shot on the subject that shows only a
  fragment of the reference plate leaks far less than a wide shot showing most of it, even at the
  same location and lighting. last_light's "hang the lantern" beat: a wide shot with the whole
  shrine tree filling the frame above her leaked 0.94-0.95 across two seeds (two different failure
  points — the static opening, then the mid-shot dimming transition — same root cause both times);
  reframing to a medium-close shot showing only one branch, not the whole tree, passed clean on the
  next seed (0.21) with the identical action and lighting. Explicit off-axis camera wording (used
  earlier on a wide symmetric corridor shot) is not reliably realized by the model — tightening the
  frame is more dependable than asking for asymmetry when the composition allows it (2026-08-23).

## Retired / not routed
Everything in ComfyUI `workflows/archive/` (95 graphs, moved 2026-08-22, not deleted). No
`api_*` templates, no `partner/` nodes, ever. Turbo LoRA (`lightx2v_turbo_4step`) and
`MiniMaxH3MemoryEfficientSageAttentionPatch` dropped from the chain graph — the first unproven on
int8, the second not installed. Each is a named upgrade with its own proof clip if ever wanted.
