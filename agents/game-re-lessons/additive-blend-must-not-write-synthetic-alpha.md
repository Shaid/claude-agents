# A synthetic/derived alpha written by an additive blend mode creates a near-zero-denominator blowup in an un-premultiply divide

**When it bites:** implementing (or reviewing) a non-standard blend mode
(additive/screen/glow) inside a rasterizer whose accumulator uses the
"blend into RGB, track coverage in a separate alpha channel, then divide
RGB by alpha at the end to un-premultiply" pattern — and the new blend
branch derives its own alpha contribution (e.g. from source luminance)
rather than reusing an alpha the ordinary "over" path already computes.

## What happened

Dragon's Crown (PS3, `vanille`)'s `FMBS` sprite-model renderer
(`tools/shared/fmbp.ts`) had a real, confirmed defect: a glow/highlight
part (bright content on a fully-black background, meant to be added, not
painted over) rendered as a solid black rectangle occluding the art
beneath it under ordinary straight-alpha "over" compositing. The fix
(`mode === 1` → additive blend) was correct in spirit: accumulate
`texel * alpha` into RGB without attenuating what's already there, so a
black source pixel contributes nothing.

The first implementation also derived a synthetic alpha for the additive
branch — `lumAlpha = max(contribR, contribG, contribB) / 255` — and
blended it into the accumulator's alpha channel the same "over" way
ordinary coverage is (`out[o+3] = out[o+3] * (1 - lumAlpha) + lumAlpha`).
This was verified against the *known* defect (the black rectangle was
gone, confirmed by direct pixel count and visual inspection) and shipped.

A second, independent check of the same rendered output found a **new**
defect the first verification pass never looked for: a solid, saturated
**green** rectangle in the exact same position the black rectangle used
to occupy. Root cause: a near-black source texel at a glow sprite's edge
still has a tiny-but-nonzero residual luminance (rounding/anti-aliasing
noise), so `lumAlpha` comes out as a very small positive number instead
of exactly zero. The final per-pixel un-premultiply divide
(`rgba[i] = acc[i*4] / a`, guarded only by `if (a <= 0) continue`) then
divides a normal-magnitude accumulated colour by that near-zero `a`,
exploding whichever channel had the larger residual numerator into a
saturated, wrong-hue pixel once clamped/rounded to 0-255.

## The fix

An additive/glow blend contribution should **only add colour**, and must
never write to the accumulator's alpha/coverage channel at all:

```js
out[o]   += cr * alpha;
out[o+1] += cg * alpha;
out[o+2] += cb * alpha;
// leave out[o+3] untouched
```

This is correct on both sides of the existing `a <= 0` guard: if nothing
has been drawn at that pixel yet (`a` still exactly 0), the added colour
is moot and the pixel is still correctly skipped as transparent by the
existing guard — no new near-zero denominator is ever introduced. If
something *was* already drawn there (the real content the glow is meant
to brighten), the divide uses that pre-existing, real alpha, which was
never at risk of being near-zero in the first place. There is no
principled way to assign an additive contribution its own coverage value
that doesn't reintroduce this exact class of bug — don't try to invent
one; just don't touch the channel.

## The generalizable verification lesson

**A fix verified only against the specific defect it was written to fix
can still ship a new, different defect in the same spot** — the first
verification pass here checked "is the black-rectangle pixel count down,
and does the image look right," which is exactly the kind of check that
misses a *different* colour artifact replacing it. After any blend/
compositing change, re-check the corpus (or at least the fixed case) for
**every** plausible artifact signature the change could introduce, not
just the one it targets — e.g. classify pixels for both "near-black
opaque" and "single-channel-saturated opaque" rather than only the
former. This generalizes past blend modes to any fix for a rendering/
compositing defect: verifying "the old symptom is gone" is necessary but
not sufficient; also check "no new symptom appeared" with an equally
concrete, quantified pixel-level test, not just a glance at the image.
