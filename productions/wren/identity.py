"""identity.py — the ONLY file a production may customise (spec §2).

Every other tool imports this. `contract.py` refuses while any required field is
blank or disagrees with beats.csv / prompts / measured audio. Do not add fields:
`drift.py` refuses any field the template does not declare.
"""

TITLE = 'Wren'                      # refused while blank
FORMAT = 'show'                     # "film" | "show"
ASPECT = (768, 1344)   # measured: every Wren ref is 768x1344 (9:16)                 # (w, h) — measured from the master ref, never typed
WORLD = ""                      # worlds/<slug> this production draws canon from, or ""

# Locked at kickoff. NegPip is the only edit point (LAWS §4). Inline <lora:name:w> syntax.
STYLE_STACK = []   # no LoRA — deliberate (Bible, Style): base Krea-2 for the natural-skin phone-shot look

# One entry per recurring character. slot is the 0-based ref_image slot → <Picture slot+1>.
# sheet paths are relative to the production folder and must be *_APPROVED_<seed>.png.
CAST = {
    "wren": {"sheet": "refs/wren_APPROVED_810003.png", "seed": 810003, "slot": 1},
    "wren_before": {"sheet": "refs/wren_before_APPROVED_811003.png", "seed": 811003, "slot": 2},
    # "wren": {"sheet": "refs/wren_APPROVED_811003.png", "seed": 811003, "slot": 1},
}

# One entry per location template (an EMPTY room; conditioning only — LAWS §8).
LOCATIONS = {
    "sunroom": {"sheet": "refs/sunroom_APPROVED_820102.png", "seed": 820102, "slot": 3},
    # "sunroom": {"sheet": "refs/sunroom_APPROVED_820102.png", "seed": 820102, "slot": 0},
}

# Byte-identical (S1)/(S2) identity phrases. Pasted by code, never by hand.
VOICES = {
    # "wren": "The soft-spoken young woman, mid-twenties, low pitch, unhurried (S1)",
}

# Measured by tools/audio.py, never typed. Empty dict = no external audio.
AUDIO = {
    # "master": "audio/master.wav", "stem": "audio/vocals_48k.wav", "duration": 167.92,
}

# Graph versions this production is pinned to. Must exist in routing.md.
WORKFLOWS = {"image": "mm_image_v1", "edit": "mm_edit_v1", "clip": "mm_clip_v1", "chain": "mm_chain_v1"}
