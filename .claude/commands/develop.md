DEVELOP (G0) for production $ARGUMENTS. Creative stage; ends in "yes" or "no".

- Write `development.md` with Ronan: the idea in a paragraph, the look in prompt words, 3-6 look-test prompts.
- Look tests are `mm_image_v1` jobs: add rows to `jobs.jsonl` (`lines` = `prompts/looktest.lines`, one prompt per line, escaped with `tools/preflight.escape`), seeds numbered from the production's seed block, `prefix` under `MovieMaker/<slug>/looktest`. Queue with `python tools/render.py <slug> . <id>`, land with `python tools/landed.py <slug> --watch`. Candidates land in `F:\MovieMaker\<slug>\refs\candidates\`.
- Show the contact sheet (the candidate PNGs). G0 is Ronan setting `status: approved` in `development.md` and committing. Nothing else starts until then.
