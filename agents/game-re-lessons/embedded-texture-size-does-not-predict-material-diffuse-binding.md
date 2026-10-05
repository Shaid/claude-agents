# A container's "biggest embedded texture" is not necessarily the one the material table actually uses as diffuse — check the binding, not the size

**When it bites:** a multi-texture container (G1T-family or similar) embeds
several textures of visibly different sizes, one format doc/prior pass
already characterized them by role from their raw dimensions/appearance
("a mask, a normal map, a low-saturation grey map — nothing with colour"),
and the next step is picking which texture(s) to swap/override/re-export
based on a size threshold (">=256px = the real one", or the reverse).

## What went wrong

Confirmed on Fire Emblem: Three Houses (`chimera`)'s class-body PACK
format. A shared class-body model's G1T texture set has 5 embedded
textures: two 4x4 placeholders and three "big" ones (512, 1024, 1024px).
An earlier pass characterized the pack as "no real colour diffuse — just a
mask/normal/grey trio" and reasoned the exported GLB's single baseColor
material must be baking one of those three "big" textures. Building on
that, a runtime/build-time diffuse-swap was first gated by `tex.width >=
256 && tex.height >= 256` — swap the "big" textures, leave the small ones
alone.

Direct inspection of the G1M material table (not the raw G1T texture
list) showed this was backwards. Every material record's type-1
("diffuse") binding resolves to texture index **0** — one of the two 4x4
placeholders — never to any of the three big mask/normal/grey textures,
which are structurally never referenced as anyone's diffuse binding at
all in this format. The size-based swap therefore replaced nothing on the
single-material packs (their one real material still resolved to the
untouched 4x4 placeholder) and, on a sibling pack with a genuine second
diffuse texture (a Dancer's real skin/face material, coincidentally also
"big"), wrongly overwrote that correct texture instead of the broken 4x4
slot. The fix had to invert the condition entirely — swap tiny (<=16px)
textures, not big ones — which correctly targeted the always-4x4 broken
diffuse slot in every pack shape probed (single-material class bodies AND
two-material Dancers) and left the Dancers' genuine secondary diffuse
alone.

## The fix

For any "which embedded resource does the material/consumer actually use"
question, resolve it from the format's own **binding/reference table**
(the material record's field that names a texture index by *role*, e.g. a
`type` enum for diffuse/normal/specular), not from the raw resource list's
own size/dimension statistics. Size correlates with "looks like a real
texture to a human," not with "is the one this specific binding points
at" — a broken/placeholder slot can be tiny while a real-but-unused
texture sits right next to it at full resolution.

## Generalization

This is a specific instance of a broader pattern: characterizing a
container's *contents* (what's inside, by inspection) is not the same as
tracing what the format's own *consumer logic* (a material table, a
dispatch table, an index field) actually selects from those contents.
Before gating any swap/override/extraction decision on a structural
property of the raw resource list (size, format, position), verify against
the actual binding/reference mechanism the consuming struct uses — one
level of indirection a size-only inspection cannot see.
