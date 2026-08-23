CUT for production $ARGUMENTS. `python tools/assemble.py <slug> <unit|.> cutNN [--head 24]` -> `python tools/cutqc.py F:/MovieMaker/<slug>/<unit>/cuts/cutNN.json` -> `python tools/tag.py .../cutNN.json`.

Deliver all three files (master, _TAGGED, _web). Never loosen a cutqc tolerance; a boundary fault means a stale segment — rebuild, do not patch. Notes come back as "slot NN, +Ns".
