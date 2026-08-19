# A part's source (u,v) may be a VRAM-upload key into a packed sibling blob, not a texture coordinate

**When it bites:** a flag/attribute-selected subset of sprite-compositing
parts renders as *plausibly-placed rectangles of garbage* (right position,
right size, wrong pixels) while the rest of the same format decodes
perfectly — especially when an undecoded sibling blob travels in the same
bundle/record, or when some flagged parts' source rects appear to "overflow"
the texture (`u+w > textureWidth`).

Confirmed on Valkyrie Profile (PSX) battle-sprite animations
(`~/Development/valkyrie`, docs/valkyrieprofile/psx/data-structure.md
§ 13.3a "Bit 13 = patch-page sampling"). Parts with flags bit 13 set never
sample the bundle's TIM at all: bits 8-10 select a blob ("page") in the
bundle's sibling `other` block, and the part's `(u,v)` is the patch's
**VRAM upload destination** — a lookup key — while its pixels live in the
blob as a tight per-rect raster. Three prior passes had modeled the symptom
as texture-edge overflow and tried wrap / mirror / clip / carry-into-V
models, all wrong for the same reason: they all sampled the resting
texture, which never held those parts' pixels. **Even an instruction-level
trace of the real GPU-primitive builder could not refute the wrong framing**
— the code legitimately computes unmasked `u+w-1` vertex UVs, because at
runtime the page *content* under those coordinates is dynamically uploaded
patch data, not the texture file's bytes. A static trace of coordinate
arithmetic says nothing about what content sits under the coordinates.

**The decisive cheap oracle — try it whenever an undecoded sibling blob
coexists with a record table carrying rect fields:** sum the tight raster
sizes of the flagged parts' *distinct* rects (here
`align4(ceil(w/2)*h)` for 4bpp) per flag-selected page and compare with the
sibling blob's exact byte size. A match is near-proof of packed per-rect
patch storage (VP1: 1,295/1,311 record-page groups matched byte-exactly
corpus-wide; alignment granularity — none/2/4 — is worth sweeping, the
right one jumped 510→1,295 exact matches).

**Decoding the packed blob when its concatenation order is unknown:** if no
closed-form order rule emerges (VP1's followed neither record-traversal nor
part-slot-major order), reconstruct it by beam search over chain prefixes —
extend each prefix with every unused rect scored *at the prefix's end
offset*, and require the finished chain to use every rect and end exactly
on the blob's last byte. The exact-partition requirement is the self-check
that makes content-guided search safe. **Scoring caveat:** a vertical/
horizontal gradient ratio mis-assigns pages dominated by sparse streak art
(speed lines, slash arcs score high on gradients even at their true
stride); an **opacity-mask row-decorrelation** metric — fraction of
transparent/opaque flips between vertically adjacent pixels, normalised by
`2·density·(1−density)` — is robust for dense and sparse art alike.
