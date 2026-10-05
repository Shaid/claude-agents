# An additive (or any non-idempotent) blend written into an oversampling forward-mapping rasterizer accumulates once per redundant sample, not once per pixel

**When it bites:** implementing or reviewing a switch from plain overwrite to
an additive/multiply/alpha-under/any accumulating blend mode inside an
*existing* rasterizer that forward-maps source texels onto destination
pixels with deliberate oversampling (dense parametric sampling steps, a 2x2
or NxN destination splat, MSAA-style supersampling) to avoid pinholes — or a
synthetic single-pixel/single-part test fixture for a new blend mode comes
back suspiciously saturated/clamped compared to the hand-computed expected
value.

## What happened

Valkyrie Profile (PSX, `valkyrie`)'s battle-animation compositors
(`composeAnimFrame` in `tools/shared/psx-vp-battle-anim.ts`, and its browser
mirror `composeFrameToRgba` in `src/data/battle-anim.ts`) forward-map each
textured quad part by walking a dense grid of `(a, c)` parametric steps
across the quad and splatting each sampled texel onto a 2x2 destination
footprint — a standard, harmless way to avoid pinholes when overwriting
(the same destination pixel gets written several times by different
samples, but every write produces the identical final RGB value, so the
redundancy is invisible).

The fix under test replaced the unconditional overwrite with a real PSX
hardware requirement — a texel whose CLUT entry carries the semi-
transparency (STP) flag must be composited additively
(`min(255, dst + src)` per channel, PSX ABR mode 1) against whatever is
already in the framebuffer, instead of overwritten. A synthetic 2x2 test
fixture with a hand-computed expected value (`dst=(200,50,10)`,
`src=(100,80,245)`, expected `min(255,dst+src) = (255,130,255)`) instead
produced `(255,255,255)` — every channel clamped to max. Root cause: the
existing oversampling scheme revisits each of the four destination pixels
somewhere between 4 and 10+ times for a small part (steps scale with
`ceil(max(spanX,spanY)*2)+2`), and every one of those redundant visits
independently added the same source colour to the accumulator, compounding
far past the one real hardware blend the primitive should produce.

## The fix

Track, per draw call (here: per *part*, since that is the unit the real
hardware draws once), which destination pixels an additive write has
already finalised, and skip any further write — blend or overwrite — to
that pixel for the rest of the current draw call:

```js
const blendedThisPart = new Uint8Array(width * height); // reset per part
...
if (blendedThisPart[pixelIdx]) continue; // already finalised for this part
if (colour.stp) {
  rgba[o] = Math.min(255, rgba[o] + colour.r);
  ...
  blendedThisPart[pixelIdx] = 1;
} else {
  rgba[o] = colour.r; // plain overwrite path, never sets the bitmap
  ...
}
```

Scoping the bitmap so only the *accumulating* write path ever sets it keeps
the fix provably inert for the pre-existing overwrite path: pixels that are
never touched by an additive write are still overwritten every redundant
sample exactly as before (last-sample-wins, unchanged), so no already-
verified pixel-exact golden output for non-blended content can regress.

## The generalizable lesson

Overwrite and any idempotent write (`dst = f(src)` with no dependence on
the prior `dst`) are invisible to redundant/oversampled writes by
construction — you can call the same pixel-write code path N times with
the same inputs and get the same final value. The moment a write becomes
**order- or count-dependent** (`dst = f(dst, src)` — additive, multiplicative,
any alpha-under compositing, exponential moving averages, etc.), every
caller of that write path that was built assuming "redundant calls are
free" needs an explicit "have I already finalised this destination unit
this draw call" guard, or the accumulation silently multiplies by however
many times the rasterizer's own oversampling/supersampling/splat scheme
happens to revisit that unit — a factor that depends on part size, quad
skew, and the sampler's own step-count heuristic, not on anything
meaningful about the content. A synthetic single-sample fixture with a
hand-computed expected value catches this immediately (a real, non-
degenerate blend result reads as `min`-clamped or otherwise saturated far
beyond what one blend should produce); a fixture built only from realistic,
large, multi-part frames can hide it inside plausible-looking output.
