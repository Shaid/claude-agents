# When a per-vertex attribute has no field-layout table at all, use triangle-strip adjacency as a real-vs-noise oracle to find it

**When it bites:** a vertex format's position is confirmed but the packed
bytes past it (normal/tangent/UV/colour/skin-weight) have no discoverable
field-layout table — the presumed descriptor structure turns out to hold
something else entirely (a name string, a material/shader-parameter table,
an unrelated record) — and a byte-range plausibility check (float in
`[-1,1]`, half-float in `[0,1]`-ish) passes for *several* candidate offsets
at once, because packed normals, skin weights and UV can all coincidentally
land in a "looks reasonable" numeric range.

Confirmed on NieR (2010, PS3)'s `VXBF` vertex buffers: the presumed
descriptor (`VXAR`, "vertex attribute array") was re-derived from scratch
and found to hold NUL-delimited shader-parameter/sampler-name text
(`"gSampler0"`, `"VariationShader-Index0"`, even the model's own name) — a
real material-binding table, but not a byte-offset/semantic/type struct.
**No in-band vertex-format table exists at all** in this format. A plain
value-range check at every 4-byte-aligned offset found multiple plausible
candidates simultaneously (several offsets all averaged a unit-length
"normal" when read as signed bytes — expected, since *any* three
independent bytes near 128 read as `(b-128)/127` average close to unit
length by pure statistics, so this test barely discriminates at all).

**The fix**: exploit a structural property real UV data has that packed
normals/weights/colour do not — **a UV pair varies smoothly between two
vertices connected by a real triangle-strip edge**, because strip-adjacent
vertices are geometrically adjacent on the mesh surface and (barring a UV
seam) sample nearby texture space. Compare the mean `|Δu|+|Δv|` between
strip-adjacent vertex pairs against the same statistic for **randomly
paired** vertices (the null control) at every candidate offset; the ratio
was 5x-32x for the real UV slot and ~1-4x (noise) everywhere else, across
every stride/group tried. The winning offset was **not a corpus-wide
constant** — different geometry groups at the *same* stride still picked
different offsets, consistent with a genuinely per-part vertex declaration
(matching the shader-parameter-name finding above) rather than one fixed
engine-wide layout, so the detector was run per record rather than assuming
a value found once generalizes.

**Verification, two independent renders, not just the ratio**: (1) plotting
every detected UV sample onto the model's own separately-decoded diffuse
texture traced the real face/body silhouette and garment-seam boundaries —
a scatter that would look uniform/random for a wrong field lands instead
exactly on the content's outline; (2) a from-scratch software rasterizer
applying the shipped pipeline's own `POSITION`+detected-UV+texture output
rendered fully recognisable, correctly-textured characters. Generalizes past
UV specifically: any per-vertex/per-record field that should vary smoothly
across a known adjacency structure (a strip, a fan, a shared-edge mesh
graph) can be *found*, not just verified, by scoring real-adjacency
smoothness against a randomized null control — stronger than a value-range
plausibility check, which coincidentally-shaped sibling fields can pass.
