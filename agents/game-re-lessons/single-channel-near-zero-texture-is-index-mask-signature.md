# A single-channel, mostly-zero texture is an index/selector mask, not a broken map

**When it bites:** An already-decoded material's texture set includes a
large (not tiny/placeholder) texture whose pixel statistics show one colour
channel isolated with a low-but-nonzero mean (e.g. green channel mean 0-7 out
of 255, red and blue ~0) while the other channels sit near zero — and its
role is unclear, or it's being written off as an unused/broken map because
"mostly black" looks like a decode failure.

## The finding

A texture that is deliberately near-black in R and B, with G holding a small
but nonzero value across most pixels and a genuinely higher value in scoped
regions, is not degenerate data — it is a per-pixel **index/selector mask**.
The shape (single channel, default-to-zero, sparse nonzero regions) is
exactly what a toon/cel-shading "which preset applies to this pixel" mask
looks like: most of a character uses shading preset 0 (the channel reads
~0), and specific material regions (hair, metal, eyes) get a nonzero
override selecting a different preset.

Confirmed on Fire Emblem: Three Houses (Koei Tecmo, Switch): a class-body
G1M material's texture-binding `type=29` slot always resolves to a large
(512/1024px) texture with mean RGB like `(0, 4.9, 0)` — R and B pinned at 0,
G non-zero but small. This exact channel shape, cross-referenced against
shader-parameter strings mined from the game's own executable
(`rampIndex`, `indexedRampMode`, `IndexedRamp` — an engine-confirmed
indexed-ramp toon-shading mode), let a previously-uncharacterized texture
binding get a real semantic role (the ramp-index override mask) from pure
pixel statistics, independent of any code trace. A sibling texture type in
the same material (`type=3`, always near-`(124,126,247)` mean, 50%+
saturation) similarly self-identified as a tangent-space normal map purely
from its flat-blue "default up vector" signature, and `type=5` (large,
R≈G≈B, low saturation, moderately bright) as a grey scalar map (AO or
specular-scaler input).

## The generalizable technique

When a material/texture-binding format has an unlabeled "type" or "role"
enum and several binding values resolve to large, real (non-placeholder)
textures, decode the actual pixels and compute per-channel mean + saturation
across a handful of real corpus instances before guessing the role from
context alone:

- **Flat, near-`(128,128,255)`-in-sRGB mean, moderate-to-high saturation** →
  tangent-space normal map (the default "no perturbation" normal encodes to
  this exact colour).
- **R≈G≈B, low saturation, non-trivial mean brightness** → a real greyscale
  scalar map (AO, roughness, specular scaler, occlusion — narrow further
  with shader-parameter name evidence if available).
- **One channel isolated, near-zero but not exactly zero, sparse regions of
  higher value** → an index/selector/mask channel, not a broken or unused
  map. Do not discard it as noise.

This is cheap (no disassembly needed) and works even when the executable
can't be reached at all — it only needs the game's own already-decoded
texture data. When executable string evidence for a matching shader
parameter (a "ramp index", "material ID", or "mask" parameter name) is also
available, the two independent signals (pixel content + parameter name)
corroborating each other is strong confirmation without any runtime trace.
