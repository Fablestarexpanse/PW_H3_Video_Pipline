"""identity.py — the ONLY file a production may customise (spec §2).

Every other tool imports this. `contract.py` refuses while any required field is
blank or disagrees with beats.csv / prompts / measured audio. Do not add fields:
`drift.py` refuses any field the template does not declare.
"""

TITLE = ""                      # refused while blank
FORMAT = ""                     # "film" | "show"
ASPECT = (0, 0)                 # (w, h) — measured from the master ref, never typed
WORLD = ""                      # worlds/<slug> this production draws canon from, or ""

# Default is NO LoRA (routing.md, LoRA policy). Inline <lora:name:w> strings only when this production
# has proven one; render.py applies them to every mm_image job.
STYLE_STACK = []

# One entry per recurring character. slot is the 0-based ref_image slot → <Picture slot+1>.
# sheet paths are relative to the production folder and must be *_APPROVED_<seed>.png.
CAST = {
    # "hero": {"sheet": "refs/hero_APPROVED_100003.png", "seed": 100003, "slot": 1},
}

# One entry per location template (an EMPTY room; conditioning only — LAWS §8).
LOCATIONS = {
    # "kitchen": {"sheet": "refs/kitchen_APPROVED_100102.png", "seed": 100102, "slot": 0},
}

# Byte-identical (S1)/(S2) identity phrases. Pasted by code, never by hand.
VOICES = {
    # "hero": "The soft-spoken young woman, mid-twenties, low pitch, unhurried (S1)",
}

# Measured by tools/audio.py, never typed. Empty dict = no external audio.
AUDIO = {
    # "master": "audio/master.wav", "stem": "audio/vocals_48k.wav", "duration": 167.92,
}

# Graph versions this production is pinned to. Must exist in routing.md.
WORKFLOWS = {"image": "mm_image_v1", "edit": "mm_edit_v1", "clip": "mm_clip_v1", "chain": "mm_chain_v1"}
