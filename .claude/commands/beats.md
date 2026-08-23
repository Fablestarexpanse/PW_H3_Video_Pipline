BEATS (G3) for production $ARGUMENTS. Write `<unit>/beats.csv` (`beat,frames,mode,refs,state_changes,cut_time`) and `slot_names.txt` (one label per beat, same order).

Rules the code enforces: frames on the 17k+5 grid (311 default, 362 dialogue/title); `refs` are identity keys separated by `;`; cut_time strictly increasing; runtime = measured audio when there is a track. Every setup paid off, every named character seen, nobody vanishes — the consistency read is Ronan's, the arithmetic is `python tools/contract.py <slug>`.

G3 is contract.py holding and Ronan approving. No render before G3.
