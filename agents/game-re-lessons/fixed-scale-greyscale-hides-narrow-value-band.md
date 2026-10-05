# A fixed 0-255 greyscale scale silently flattens a narrow palette-index band into an invisible block

**When it bites:** rendering an unfamiliar palette-index/intensity buffer as
greyscale for visual verification (Method §3's "render greyscale first"),
specifically for a format where the real index range can sit anywhere in a
larger space rather than always spanning close to the full 0-255 domain —
e.g. a 4-bit nibble value plus a per-image bank/offset byte (`palOffset +
nibble`), a sub-range palette selector, or any indexed format with a
variable base. A visual inspection that comes back "looks like a flat/empty
block" is not automatically evidence the decode is wrong or the content is
blank — it may be a rendering artifact of the greyscale mapping itself.

## What happened

Ishar's (Amiga AGA) sprite decoder (`ishar-sprites.ts`) resolves 4-bit
pixels as `palOffset + nibble` (nibble 1-15, `palOffset` a per-image 16-color
bank selector into a 256-color AGA palette). Its existing greyscale
visualization used a single fixed formula, `grey = 40 + (index/255)*200`,
which assumes the index spans close to the full 0-255 range. For a
backdrop/environment sprite with `palOffset` around 80-86, the real decoded
indices only ever span roughly 87-101 (~15 possible values) — a real,
non-degenerate index range with genuine spatial structure — but the fixed
formula compressed that whole band into about 11 adjacent grey levels out of
256, rendering the sprite as a visually flat, texture-less block. This
looked exactly like "no real image data here, just a filler rectangle,"
which would have wrongly disqualified real content (or, worse, been
misdiagnosed as a decode bug and sent debugging effort into the wrong
layer — the pixel decoder was fine; only the visualization was lossy).

**How it was caught:** a raw index-value histogram on the suspect bitmap (9
distinct values, well-distributed across the whole image, not one repeated
constant) proved the underlying decode was fine before touching any
rendering code — cheaper and more decisive than staring at a flat-looking
PNG.

**The fix:** add a per-bitmap min-max-stretch greyscale function alongside
the fixed-scale one — normalize against the image's OWN observed
non-transparent index range, not a hardcoded 0-255 assumption — and use the
normalized version specifically for verification/legibility renders. Keep a
fixed-scale version only where cross-instance greyscale comparability
matters more than any single image's legibility (e.g. a shared corpus-wide
sprite atlas where "compare relative brightness between two different
sprites" is a real use case) — do not silently drop that use case by
replacing it outright.

**Generalizes to:** any indexed/paletted format being visualized without its
real color table (arcade tile ROMs, old console/PC 4-bit-plus-bank formats,
depth/height maps, any bank-offset palette scheme) — a "looks blank/flat"
render is not evidence of missing content until a raw value histogram rules
out a narrow-range visualization artifact.
