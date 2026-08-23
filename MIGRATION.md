# Migration manifest — old vault → v2 repo

Read from `C:\Users\Brian\Documents\Feyndral\Movie Maker`; never write to it. Copy, don't link.
Everything below is already ported in `port/` except the rows marked **copy** or **convert**.

## Ported (done, in this folder)
| Source | Destination |
|---|---|
| Prompting Laws + H3 Combat and Action Style + Session 08b "lost rules" + Wren double-anchoring | `LAWS.md` |
| Reference Sheet Prompts + Baseline Guide + Reference Approval Gate + R-018/R-030/R-035 | `.claude/skills/reference-sheets/` |
| Ref2VA Clip Prompt Template + H3 Prompting Guide (voice locks, chain scenes) | `templates/clip_prompt_template.md` |
| Model Routing (grid, formula, calibration, stacks) + Workflow Registry routing table | `routing.md`, `costs.csv` |
| Workflow Registry (tnew, audio split, demucs) + Assembly Guide + comfy-draftsman findings | `RUNBOOK.md`, `.claude/skills/assembly/` |
| Wren Production Bible format sections | `templates/formats/reel.md` |
| Templates folder field lists | `templates/production/` |
| Every repeated Learning Log finding | `findings.jsonl` |

## Copy — code
| Source | Destination | Change |
|---|---|---|
| `F:\stems\moviemaker_tools\clipqc.py` | `tools/clipqc.py` | keep frames / ref-leak / blown / black / cuts; replace whole-frame grade with local block stats; add `--selftest` against `calibration/` |
| `F:\stems\moviemaker_tools\make_tagged.py` | `tools/tag.py` | unchanged method; read `slot_names.txt` from the unit folder |
| `PW_ColorTools` | stays in `mm_image` back end | — |
| `h3-prompt-writing` skill | `.claude/skills/h3-prompt-writing/` | unchanged |

## Copy — approved references (PNG + prompt from Bible or PNG metadata + seed → `refs/manifest.json`)
| Asset | Seed | Destination |
|---|---|---|
| Lan turnaround | 800031 | `worlds/fablestar/refs/` |
| Mira turnaround | 800042 | `worlds/fablestar/refs/` |
| Amias turnaround | 830004 | `productions/wttb/refs/` |
| Club interior template | 830140 | `productions/wttb/refs/` |
| Amias grill/face tight crops, Yara face, girls green/silver | per Registry v7 | `productions/wttb/refs/` |
| Wren turnaround | 810003 | `productions/wren/refs/` |
| Wren before-state turnaround | 811003 | `productions/wren/refs/` |
| Wren master wide (accepted, crop issue) | 820005 | `productions/wren/refs/` (status: candidate) |
| Sunroom template | 820102 | `productions/wren/refs/` |
| Base-look outfit flat-lay | 820201 | `productions/wren/refs/` |
| Bōzu cast (Kaito 900004 · Mirin 900104 · Kenji 900202 · Hina 900301 · Tomo 900401 · Nao 900501 · Sube 900601 · Chiyo 900701 · Yuki 900801 · Ganta 900901 · Carp 901001) | as listed | `productions/bozu/refs/` (all status: candidate) |

## Convert — content
| Source | Destination |
|---|---|
| Bōzu Production Bible cast + premise + humour rules | `productions/bozu/brief.md`, `characters/*.md` |
| Bōzu Opening (OP) v1 rev 3, scenes 1–5 | `productions/bozu/S01E00 - Opening/beats.csv` + `prompts/opening.lines` (chain) |
| Bōzu Voice Locks rev 2 | `productions/bozu/identity.py: VOICES` |
| WTTB Shot List v1 / Timing Map / club board prompts (wttb_v11_prompts.txt) | `productions/wttb/beats.csv`, `prompts/club.lines` |
| Wren Dark Muse 11 beats + piece-by-piece 8 beats (verbatim in the Bible) | `productions/wren/S01E01 - Dark Muse/prompts/` — first preflight calibration set |
| Fablestar Expanse / Perpetua / Greymoor canon folders | `worlds/<world>/` |
| Dead Signal Production Bible | `productions/dead_signal/brief.md` — **decide**: own film or Fablestar episode |

## Decide once during migration
- Dead Signal vs Fablestar Expanse: one production or two.
- `MiniMaxH3MemoryEfficientSageAttentionPatch`: install / swap / drop.
- The six superseded Bōzu trailer clips: keep on F: as evidence or drop.
- The three Bōzu cast members cut from the OP (Sube, Chiyo, Yuki): still in the show.

## Leave behind
Movie Maker OS · Rules numbering · Learning Log narrative · Bible session transcripts ·
`measure_vo.py` · Session 06 references · all 33 ComfyUI workflows (archived on the
instance, not deleted) · every "proposed, Ronan to ratify" item.
