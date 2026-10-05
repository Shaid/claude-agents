# A cloth/procedural submesh's "vertex attributes" may be solver input, not geometry — reading Position as positions collapses the mesh onto its anchor and looks like missing content

**When it bites:** user-confirmed real in-game content (long hair, a cape, a
skirt) extracts short/cropped/collapsed while every census says no other
geometry exists anywhere in the corpus; or a submesh's decoded "positions"
cluster near the origin / one bone while its siblings decode fine; or a
mesh-group/submesh record has a small "type"/"cloth"/"physics" field the
parser currently skips. Also: a vertex's "joint indices" overflow the
submesh's own bone palette (e.g. values 0..23 against a 1-slot palette) —
that is a tell the indices belong to a *different* index space entirely.

## What went wrong

Fire Emblem: Three Houses (chimera, Koei Tecmo G1M): Lysithea/Dorothea/
female Byleth's long hair, Sothis's hip-length cascade and Manuela's cape
were "missing" from every exported GLB despite months of censuses proving no
unclaimed geometry existed anywhere (DLC decrypts, orphan-pack sweeps,
executable RE). The answer was in the already-extracted packs all along: the
mesh-group entry carries a `clothType` field the parser skipped, and when
`clothType == 1` **every vertex attribute is repurposed as cloth-solver
input** — Position becomes a control-point weight vector, BoneWeight/Color
become center-of-mass weights, BoneIndex/PSize/Fog/UV(u8x4) become four
control-point index sets, Normal becomes basis coords + a depth scalar.
The real geometry only exists after evaluating the solver formula against a
separate driver-mesh control-point section (Koei's `NUNO`/`NUNV`; the
control points' rest positions are `world[entryParentBone] x storedNodePos`).
Decoding the attributes at face value produced near-origin "positions" that
skinning then parked on the anchor bone — rendering as plausible short hair,
not as visible garbage. 170/569 model packs were affected (every character
with dangling cloth), not the 3 characters the bug reports named.

Two secondary traps from the same investigation:

- **Posed-bounds math on repurposed attributes fabricates evidence.** An
  early probe transformed the raw "positions" by per-vertex "joint" lookups
  and got convincing full-length-hair bounding boxes — an artifact of weight
  values being fed through transform math. Never trust bounds/statistics
  computed from attributes until the submesh's type field is known.
- **A relisting group cluster can carry a zeroed/garbage copy of the type
  field.** The same submesh index appeared in a second lod-0 group cluster
  with `clothType 0` (or byte-shifted garbage) — a plain "last write wins"
  map silently demoted every cloth submesh back to the collapsed path. Only
  let a real cloth value claim the slot; never let a non-cloth relisting
  overwrite one.

## The fix

Parse the type field; for procedural submeshes, port the reference
implementation's evaluation (here Project-G1M's Noesis plugin) and bake at
rest pose; verify by (1) numeric diff against the reference algorithm and
(2) a render matched against the user-confirmed in-game look. Bind the baked
result bind-relatively (skin IBM = `inverse(world[anchorBone])`) so it is
exact at bind and follows the anchor under animation. Expect one honest
residual: garments authored as flat pattern sheets (Manuela's cape) bake
spread out — the reference implementation produces the identical rest
positions; the draped in-game shape is the runtime solver's equilibrium and
is not recoverable by any static decode.

Generalizes to any engine with GPU/CPU-evaluated cloth, morph, or spline
geometry (Koei NUN, PhysX cloth cooked assets, hair-strand systems): when a
format has a per-submesh "type" discriminator, decode it FIRST — attribute
semantics are only trustworthy for the default type.
