# A quad's UV record and its face-index record can use different vertex winding orders

**When it bites:** a textured-quad format stores two parallel per-face
arrays — a face/vertex-index record and a separate UV-coordinate record —
and a texture bake or render built by reading both in the same raster
order (`0,1,2,3`) produces a self-intersecting "bowtie" polygon: no crash,
no bounds error, just visibly scrambled/interleaved output where you
expected a clean quad.

Confirmed on Parasite Eve (PSX)'s actor-model format: the face-index array
already used PSX-standard triangle-strip-style quad winding `(v0,v1,v3,v2)`
(the two triangles of the quad share an edge, not a diagonal split read in
raster order), but the UV record for the same quad is stored in plain
raster order `(u0,v0),(u1,v1),(u2,v2),(u3,v3)`. Reading the UV array
straight through and pairing it positionally with the already-rewound
index order produced a polygon whose edges crossed rather than forming a
simple quad — a scanline "UV-space unwrap" texture bake (draw the polygon
at its own stored UV coordinates, sample the source texture at the same
(x,y)) filled a bowtie-shaped region instead of a clean rectangle, giving
scrambled/interleaved-looking output that still technically "succeeded"
(no exception, no out-of-range index).

**The fix generalizes:** whenever a format pairs two independently-stored
per-face arrays describing the same polygon (index order, UV order, colour
order, normal order...), verify each array's *own* winding convention
separately before assuming they're positionally aligned. Don't assume a
UV/colour/normal record inherits the winding already confirmed for the
index record — re-derive or re-wind it to match (here: re-index the UV
array as `[0,1,3,2]` before use, exactly mirroring the index array's own
already-confirmed reordering) rather than consuming it in raw file order.
A render/bake that "succeeds" with no error is not evidence the winding is
right — only a pixel-exact comparison against an independent reference
render caught this.
