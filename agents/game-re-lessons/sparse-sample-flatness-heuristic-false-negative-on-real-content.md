# A coarse sparse-sample "flatness"/uniqueness heuristic false-positives on real, low-color-diversity texture content

**When it bites:** a pipeline skips "essentially blank/placeholder" texture
or image assets via a cheap heuristic — sample a few hundred pixels at a
stride, count distinct colour values, treat a low count as "flat, skip
it" — applied to real game art (armor/clothing textures, flat-shaded UI
elements, anything with one dominant fill colour across most of its UV
space), not just genuine blank placeholders.

## What went wrong

Confirmed on Fire Emblem: Three Houses (`chimera`)'s texture-export
pipeline (`build-assets.ts`'s `isFlat()`):

```js
function isFlat(rgba) {
  const step = Math.max(1, Math.floor(rgba.length / 4 / 256));
  const seen = new Set();
  for (let i = 0; i < rgba.length; i += step * 4) {
    seen.add((rgba[i] << 16) | (rgba[i+1] << 8) | rgba[i+2]);
    if (seen.size > 4) return false;
  }
  return true;
}
```

~256 sparse samples across a 1024x1024 texture (a ~4096-pixel stride), and
"flat" if fewer than 5 distinct exact RGB triples turn up in that sample.
This heuristic exists to catch genuine placeholder/blank DATA0 entries —
and does, for those — but it also silently dropped **47 of 1,134 real,
corpus-confirmed character-armor palette-variant textures**: a class-body
recolor texture with one dominant armor colour spread across most of a
1024x1024 UV atlas can easily land <=4 distinct RGB values in a sparse
256-sample draw even though it's genuine, non-placeholder art (skin tone,
trim, metal, cloth all present, just spatially minor relative to the
dominant fill). No error, no log line distinguishing "genuinely blank" from
"heuristic missed the minority colours" — both silently produce zero output
files, and the only way the gap surfaced was an explicit disk census
against an independently-known expected count (1,134/1,152 from a prior
byte-level corpus scan), not from the pipeline's own run output.

## The fix

Don't tune the general heuristic against one content class's statistics —
that just shifts which real content it misses next. Instead, exempt a
range/category of entries **already independently confirmed to be real
content** (via a structural/byte-level census done separately from this
heuristic) from the flatness check outright, and keep the general
heuristic for everything else it was actually designed to catch (genuine
blank/degenerate placeholder entries elsewhere in the corpus, which still
need it).

## Generalization

Any coarse statistical "is this real content or filler" classifier that
samples sparsely and thresholds on a small count (distinct colours, distinct
byte values, non-zero fraction) is vulnerable whenever real content can be
spatially or value-dominated by one class (a large flat-colored region, a
mostly-silent audio clip, a mostly-background sprite frame) — the *rare*
minority signal is exactly what a sparse sample is likeliest to miss. Before
trusting a "skipped N assets as filler" pipeline log line, cross-check its
skip count against an independent expected-count oracle for at least one
suspicious content class, not just eyeball the skip rate as plausible.
