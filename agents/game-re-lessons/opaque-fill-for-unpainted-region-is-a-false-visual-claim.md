# Filling unpainted pixels with opaque black to avoid "claiming" transparency makes a *stronger*, false visual claim than transparency would

**When it bites:** compositing a sprite/tile-scatter/partial-coverage render
into an RGBA canvas, where some canvas area is genuinely outside the
decoded content's own authored coverage (a room's tile bounding box, a
sparse sprite atlas cell, a partial VRAM reconstruction) — and the
temptation (often written as an explicit code comment) is to fill that
area with opaque black rather than `alpha=0`, on the reasoning that
"rendering it transparent would be a claim about the game's own
compositing/blending this decode cannot make."

## What happened

Parasite Eve (PSX, `~/Development/parasite`)'s tile-scatter background
compositor (`tools/parasiteeve/actor-background-scenes.ts`) filled its
whole output canvas with opaque black (`alpha=255` everywhere, RGB
defaulting to 0) before painting any tiles, with exactly this reasoning in
a code comment: unpainted regions are genuinely outside the room's
authored tile coverage, so claiming transparency would overstate what's
known about the game's real compositing.

In practice this produced the opposite of the intended caution. A
corpus-wide pixel census found 42/509 shipped images were >=95% solid
black by area (6 of them 100% — indistinguishable from a blank or broken
render), and several "good" renders had visible black margins/dead
corners where real content should show through to nothing. A person
looking at the output reasonably read solid black as "this is broken" or
"this pixel is really black" — a *specific, false* visual claim about the
pixel's colour. Filling with `alpha=0` instead makes no claim at all about
colour or about the game's own runtime blending; it states only the one
fact the decode actually knows: no tile data was decoded for this pixel.
That is strictly more honest, not less, than opaque black.

## The fix

Default the canvas to fully transparent (a freshly-allocated typed array
already zero-fills, so this needs no explicit loop) and set `alpha=255`
only at the point a pixel is actually painted from real decoded data:

```js
const rgba = new Uint8Array(width * height * 4); // alpha already 0 everywhere
for (const tile of tiles) {
  // ... sample real pixel data ...
  rgba[o + 3] = 255; // only here, when something real is drawn
}
```

Verify the consuming viewer/engine actually respects PNG/canvas alpha
before relying on this (it almost always does — Canvas2D `drawImage` and
`<img>` both composite alpha natively with no extra work — but confirm by
reading the actual render path rather than assuming).

## The generalizable lesson

"Don't claim something the decode can't prove" is the right instinct, but
apply it to the *strongest* available neutral statement, not to whichever
option merely avoids the specific claim you're worried about. Alpha=0 and
opaque-black are not two equally-neutral choices — one is a true statement
("no data here"), the other is a false one ("this pixel is black"). When
a defensiveness-motivated fallback is being chosen between two options,
check which one is actually neutral by asking what a viewer would
conclude from it, not just whether it avoids asserting the specific fact
you set out to avoid asserting.
