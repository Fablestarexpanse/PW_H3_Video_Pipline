Create a production. Ask for nothing that is already in the arguments; refuse to create one by hand.

`python tools/new_production.py <slug> --format film|show --title "<Title>" [--unit "S01E01 - <name>"]`

Then open `productions/<slug>/identity.py` and fill only what is known today (WORLD, STYLE_STACK). Leave CAST/LOCATIONS/VOICES/AUDIO empty — they are filled at their gates by code, never typed ahead. Run `python tools/drift.py <slug>` and `python tools/status.py`.
