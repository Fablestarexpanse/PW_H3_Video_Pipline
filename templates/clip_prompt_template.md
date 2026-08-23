# Ref2VA Clip Prompt Template

Ported from the vault's *Ref2VA Clip Prompt Template* (distilled from 40+ shipped WTTB clips and the
Fablestar A1 techniques). The block **order** is the order that stopped each failure — keep it.
Structure and field names come from the `h3-prompt-writing` skill; this template fixes what goes
*inside* `retention_analysis`. `preflight.py` refuses more than **16** named blocks (LAWS §10) — this
template IS the 16. Delete blocks that do not apply; never add a `SCALE STATE`.

One prompt per line in `<unit>/prompts/<unit>.lines`, escaped with `tools/preflight.escape`; frames come
from `beats.csv`, never from a duration widget.

Changed from the vault version (LAWS §3/§8, measured): **no "never shown / never reproduced" clauses**.
The exclusion stops citation, not copying — the plate was reproduced at +0.97 with that clause present.
The fix is the positive frame-zero sentence, so block 1 is written positively.

---

## subject_definitions:

```
<Picture 1> is <what the image IS, physically — a tight macro, a turnaround sheet, a survey
photograph>. Only <THE ONE THING TAKEN> is taken from <Picture 1>; its background and framing
belong to it alone.

<Subject 1> is the man/woman defined jointly by <Picture 1> for <X>, by <Picture 2> for <Y>,
and by <Picture 3> for <Z>. <One sentence of build, age, hair, skin, eyes.> <One sentence of
wardrobe, itemised — every item that must persist.>

<Picture 4> is a survey photograph of <the place>, supplied so <what it is for> can be reproduced
accurately: <the description>. THE <ATTRIBUTES YOU WANT> OF <Picture 4> ARE THOSE OF THIS CLIP. ONLY
<WHAT IS TAKEN> IS TAKEN FROM <Picture 4>: its emptiness, its framing, its camera position and its
lighting stay in the photograph.

<Subject 2> is the woman in <Picture 6>: <distinguishing hair colour, hair length, garment colour —
a face alone is not enough>. She is a completely different person from <Subject 1>: <the contrast,
as a pair>. The two are never confused for one another.
  -- or, when absent --
<Subject 2> is the woman in <Picture 6>. She does not appear in this clip.

<Audio 1> is the lip-sync reference track for this clip, containing English vocals: <a male lead /
a male lead for the first N seconds only, then a female voice which <Subject 1> does not mouth>.
```

## summary:

```
[reference generation + audio reference] <THE CAMERA SHAPE IN CAPITALS — ONE UNBROKEN LATERAL
TRACK / ORBIT / DESCENT / LOCKED MEDIUM>. <One sentence of what happens.> <If the camera is locked,
say so here — the first of three times.>
```

## retention_analysis:

```
1 · REFERENCE USE STATE: THE FIRST FRAME OF THIS CLIP IS ALREADY <a positive description of frame
    zero — framing, height, what fills the edges> — it is him, at chest height, with <what fills the
    edges>. <Picture 4> is conditioning: its architecture is the architecture of every frame, and
    every frame is <OCCUPANCY: "packed with people wall to wall from the very first frame to the
    last" / "a working kitchen with every surface in use">. If any frame shows <the failure>, that
    frame is WRONG.
      (mode ref2va-master, the reel format: "THE FIRST FRAME IS <Picture 1>, the locked master wide,
       exactly as framed" — preflight then requires <Picture 1> named here, and clipqc --expect-master
       refuses a clip that does not open on it.)

2 · <Picture N>: fully_preserved / partially_preserved - <what must survive, and where it is
    visible>. This overrides any tendency toward <the model's default>.

3 · WORLD STATE: the architecture, materials and proportions, stated as always-true. Include a
    CEILING / VOLUME clause if height is ever wrong, and a both-things-at-once clause for a hybrid.

4 · GRADE STATE: <exposure, contrast, grain, the only colours>. Say what the grade IS in every frame.

5 · LIGHT STATE: name each source AS A PHYSICAL OBJECT and where it is mounted. Beams need an
    emitter ("laser projector units bolted to the stage, all beams converging there").

6 · WARDROBE / CROWD STATE: a POSITIVE list of what everyone is wearing. A positive list leaves
    nothing for the unwanted garment to be.

7 · FRAMING STATE, and it overrides every instruction about scale in this prompt: <Subject 1> is
    framed from the <WAIST/CHEST> UP or closer for the ENTIRE clip and HIS HEAD FILLS AT LEAST <A
    QUARTER / A THIRD> OF THE FRAME HEIGHT IN EVERY FRAME. The size of the venue is proved by what
    is visible ABOVE AND BEHIND HIM in the upper third of frame. If a frame shows the room and he is
    small in it, that frame is WRONG.
      -- SIZE BY IN-FRAME ANCHOR beats a fraction wherever legibility is not the point:
         "no taller in frame than the rubble heaped at their bases".
      -- when the camera must travel, use a FRAMING SCHEDULE: his size in frame at named timestamps,
         monotonic, with a final test ("if his face is small at the end of this clip, it is wrong").

8 · CAMERA STATE - THE ONLY CAMERA INSTRUCTION IN THIS CLIP AND IT OVERRIDES EVERY OTHER ONE.
    <One shape, as a rule the model can satisfy continuously.> There is exactly one camera move in
    this clip and this is it. (Second statement of a lock — LAWS §11.)
      Shapes proven to hold: locked-off medium · backward track at his walking pace so he stays the
      same size · single-direction orbit at arm's length · descent ending close on the face.

9 · ONE-SHOT STATE: THE ENTIRE CLIP IS ONE SINGLE UNBROKEN CONTINUOUS SHOT, one lens, one place.
      -- if there must be cuts, a CUT STATE shot budget instead: each shot's absolute duration, a
         comparative ranking ("the SHORTEST shot in the clip"), and an overrun rule ("if any shot is
         running long it is cut anyway at its stated time"). A list of cut times alone is not enough.

10 · MOVEMENT / STILLNESS STATE: what the body does for the whole clip, in one rule. "He walks
     steadily for the whole clip and keeps walking while he speaks" beats any number of beats.

11 · MOUTH STATE: his mouth moves ONLY during <exact windows>. At every other moment his lips are
     closed and his jaw still, including <the head bed>. He is the only person who mouths anything.
     <EXEMPTION when the mouth does something else: "between 00:0X and 00:0Y his mouth is clamped on
     her neck; the lyric continues over the action.">

12 · ACTION STATE(S) - one per significant action, each with a START and END POSITION and a
     monotonic direction ("her height above the floor decreases continuously and at 00:11.600 and
     in EVERY FRAME TO THE LAST she is crumpled on the floor. THE CLIP ENDS ON THIS IMAGE.").
     For any two-body action: ORIENTATION stated positively · a NAMED SIDE · every limb placed · a
     whole-frame test ("if a frame looks like two people kissing, it is wrong"). If the action is
     the point of the clip: IT IS SHOWN ON CAMERA, IN FULL VIEW, and it holds for <duration>.

12b · ABSENCE BY POSITIVE EQUALITY - "exactly as dark as the ink of the linework around them" ·
      "a smooth blank ovoid, bare and unbroken like a frosted lamp bulb" · "plain bare skin from
      elbow to wrist, the same clean skin as the backs of her hands".

13 · CONTINUITY STATE(S) - blood, props, costume, damage: timed, with the anti-tidying clause
     ("it REMAINS after the wipe, unchanged, in every frame that follows").

14 · REACTION STATE: who notices and who does not, as an absolute ("the dancing closes over the
     gap within half a second").

15 · LOCATION STATE: what the background IS in every frame ("the same timber-and-brick hall, its
     trusses and crowd visible behind him in every frame to the last").

16 · <Audio 1>: reference - only the vocal timing and lyric content are referenced, to drive mouth
     movement. The signal is not copied.
```

## detailed_description:

```
<ONE opening sentence: what the video is, where it is set, AND the shot structure.>
<The world paragraph: materials, light sources, grade, "real skin texture, like a live-action
feature".>

[Shot 1 - the only shot] THE VIDEO OPENS <positive frame-zero sentence, matching block 1 word for
word in substance>. <The camera is locked — third statement.> <His lips are shut for the first N s.>

When <Audio 1> reaches the phrase <d>[English] <THE LINE VERBATIM></d>, which runs from 00:0X.XXX
to 00:0Y.YYY, <Subject 1> mouths the words in exact sync for that whole window, lips shut before
and after, jaw, lips and tongue matching every syllable. <One sentence of what he does meanwhile.>

At 00:0X.XXX, <what happens>.

On the final frame <what is true>; the picture holds to the last frame.
```

## overall_soundscape:

```
<Dynamics language: near silent between beats, hard transients on impact — or:> The target video
carries no generated audio; its soundtrack is laid over the picture externally.
```

## non_diegetic_music:

```
<The score, or:> No score is generated; the music is added externally.
```

---

## Before you queue it — `python tools/preflight.py <slug> <unit|.> <file.lines>`

It refuses the three that cost the most: a discretion clause (LAWS §3) · a bare negative list
(LAWS §4) · `SCALE STATE` (LAWS §2); and frame zero missing, >16 blocks, sections out of order,
an unapproved `<Picture N>`, a blank line, CRLF, or a line that does not survive the unescape.
It advises when a camera lock is stated in fewer than three sections (LAWS §11).
