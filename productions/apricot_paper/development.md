---
status: draft
---
# Apricot Paper Story — Development

## The idea
A Redwall-shaped story — mice of a woodland abbey, their feasts, their walls, their enemies — written for
adults: the violence has weight, the politics are real, the warmth is earned. Anthropomorphic mice (and the
creatures around them) in a hand-made world of stone, oak, wool and candle-light.

## The look, in prompt words
Illustrated storybook realism on warm apricot-toned paper: visible paper grain and fibre, ink linework with
watercolour and gouache washes, soft vignetting at the edges, pigment pooling in the shadows, warm candle and
hearth light, muted ochre, umber, moss and slate palette with one saturated accent per image. Fur rendered as
drawn strokes, never photographic. Every still (character sheets, props, locations, master frames) carries
the `ApricotPaper_Krea2_V1.0` LoRA — this production's `STYLE_STACK`; no other LoRA.

Clips (H3) take the look from these stills as `<Picture N>` references; H3 carries no LoRA.

## Look tests (G0)
Five stills, `mm_image_v1`, 1344×768, seeds 110001–110005, the LoRA at 1.0 and one repeat at 0.8 to settle the
weight. They land in `F:\MovieMakerpricot_paperefs\candidates\`. Ronan answers yes / no / "neither, go X".

| Seed | Weight | Subject |
|---|---|---|
| 110001 | 1.0 | A scarred grey mouse veteran, full figure, at a rain-dark abbey gate at dusk |
| 110002 | 1.0 | The abbey great kitchen, empty, hearth lit, copper pans, a long oak table |
| 110003 | 1.0 | A prop: a mouse-scale short sword with a wrapped leather grip on apricot paper, nothing else |
| 110004 | 1.0 | Wide: the abbey on its hill above autumn woods, smoke from two chimneys, evening |
| 110005 | 0.8 | The same veteran as 110001, same prompt, LoRA at 0.8 — the weight comparison |

G0 ends with `status: approved` here, and the chosen weight written back to `identity.STYLE_STACK`.
