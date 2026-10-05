# A pixel-format numeric value matching a known SDK enum by coincidence isn't a confirmed format

**When it bites:** A texture/pixel descriptor stores a small integer
"pixel format" field, and its value happens to coincide with a real,
well-known SDK enum's numbering for at least one observed value (e.g. `4`
matching `GU_PSM_T4` on the PSP), tempting the assumption that *every*
other observed value also follows that same enum (`8` -> `GU_PSM_DXT1`,
because that's what pspgu.h's `GU_PSM_*` list says comes after the
indexed formats). The coincidence is real for the one value that was
actually checked against a render; it is not evidence for the others.

## What happened

The 3rd Birthday (PSP)'s `pack` container texture descriptors carry a
`pixelFormat` field with two observed values, `4` and `8`. A `4` renders
correctly as `GU_PSM_T4` (4-bit indexed, 16-color CLUT) — genuinely
confirmed by render (legible in-texture text). A prior pass then assumed
`8` must be `GU_PSM_DXT1`, because that's the pspgu.h SDK header's own
enum value for DXT1 (`GU_PSM_5650=0, ..., GU_PSM_T32=7, GU_PSM_DXT1=8`).
That assumption was never independently checked against real bytes and
was documented as a parenthetical ("PSP `GU_PSM_*`: 4 = GU_PSM_T4, 8 =
GU_PSM_DXT1") rather than flagged as unverified.

The real check — computing the payload's own byte length from the chain-
closure oracle already used to confirm T4 (`nextDescriptor.clutStart -
thisDescriptor.clutEnd`) — showed every `pixelFormat == 8` texture's real
on-disk payload is **exactly `width * height` bytes** (1 byte/pixel), not
`(width/4)*(height/4)*8` (real S3TC/DXT1's 0.5 bytes/pixel) or even
`(width/4)*(height/4)*16` (DXT3/DXT5's 1 byte/pixel — which numerically
matches by coincidence, but decoding real bytes that way produced pure
noise, ruling it out too). Meanwhile the fixed-size region the T4 format
already established as "the CLUT" was a constant 1024 bytes regardless of
texture dimensions — exactly `256 * 4`, a full 256-entry RGBA8888 CLUT.
Both facts point the same direction: this is `GU_PSM_T8` (8-bit indexed,
1 byte/pixel, 256-color CLUT), which in the *real* pspgu.h enum is `5`,
not `8` — the game's own `pixelFormat` field isn't the pspgu enum at all,
it empirically equals the format's **bit depth** (`4` -> 4bpp, `8` ->
8bpp), a much simpler and self-consistent convention that a sibling format
(`T4`) had already hinted at without anyone checking whether it
generalized.

Rendering sealed it: decoding the same bytes as DXT1/DXT3/DXT5 (with or
without a swizzle pass) produced unstructured noise on every sample;
decoding as T8 (same swizzle formula as T4, just `rowBytes = width`
instead of `width/2`, and a 256- instead of 16-entry CLUT) produced
immediately recognizable game art — a sky/cloud gradient, a night
skyline, a Christmas-tree scene, organic creature-flesh textures with
glowing eyes.

## The fix

Never accept "this format's numeric tag equals a well-known SDK enum's
value" as confirmation for more than the single value you've actually
rendered and checked. Before trusting the mapping for a second value:

1. Re-derive the real per-instance payload size from a structural oracle
   already proven for a *different* value of the same field (here: the
   chain-closure invariant that made T4 corpus-wide confirmable). Compare
   that size against every format hypothesis's own formula — a
   half-or-double mismatch is a hard, dispositive signal before any pixel
   is decoded.
2. Look at the raw bytes directly. Compressed block formats (DXT1/3/5)
   have close-to-uniform-random color/alpha/index bits for continuous-tone
   art; a plain indexed format's raw bytes are index values into a
   separately-stored palette and can look deceptively smooth/gradient-like
   when the palette itself is smoothly ordered (as a sky-gradient CLUT
   naturally would be) — don't mistake a "smooth-looking byte run" for "not
   compressed" without checking the *decoded* image, but do let it
   motivate trying the simpler hypothesis first.
3. Render every real format candidate and require a coherent image, not
   just "no crash" or "plausible byte count." A wrong format can still
   consume the exact number of bytes you expect (DXT3/DXT5's 16 bytes/block
   happened to numerically equal T8's `width*height` here) while producing
   garbage pixels.

## Generalizable takeaway

A format's own numeric tags are frequently *not* a vendor SDK's literal
enum, even when one or two values happen to coincide — reverse-engineered
in-house formats often reuse a simpler internal convention (bit depth,
byte stride, a small ordinal) that only looks like the SDK enum by
accident for the values you happened to check first. Confirm every
distinct tag value against real bytes and a real render independently;
don't extrapolate a working single-value match across an entire enum
family.
