# A per-chunk record array may be alternatives (LODs) or parts (draw batches) — test per-record footprints before rendering just one

**When it bites:** a geometry chunk carries a small fixed-count array of
sub-mesh records (each with its own vertex list/index map and face
counts), the records got labelled "LOD table" (or "detail levels",
"variants") by analogy rather than by tracing the consumer, and an
exporter/viewer is about to render exactly one of them — especially when
an automated "looks plausible" screenshot check has already blessed that
single-record output.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project,
`data-structure.md` §9.6.1 Correction, commit 9c2b8bd): each world-map
terrain chunk's four 20-byte records were documented as a "LOD table" and
the exporter emitted `records[0]` only — silently dropping ~68% of the
map's faces. Every prior verification passed anyway: **each record alone
renders as individually-plausible terrain patches**, so the automated
screenshot check judged the quarter-coverage patchwork "coherent
continents", and the doc's own "whole composed map" evidence artifact
turned out to be exactly record index 1's totals. Only a human's "nothing
recognizable" report exposed it. The records are actually
**spatially-disjoint draw batches** that jigsaw into the full cell —
forced by a hardware ceiling that was in plain sight the whole time: the
PSX scratchpad limits each record to ≤124 transformed vertices while the
chunk's shared pool holds ~300, so **no single record could ever cover a
whole chunk**.

**The discriminating measurements are cheap — run them before choosing a
consumption rule:**

- **Per-record spatial footprint**: bbox/2D-render the vertices each
  record actually references (via its own index map). Same footprint at
  decreasing density = real LOD alternatives → render one. Disjoint
  jigsaw footprints whose union tiles the region = parts/batches →
  render all. (VP1: batch face totals 4730/5174/4517/470 — real LOD
  chains decay monotonically, this doesn't; cross-record duplicate faces
  2/14,891 — an effective partition.)
- **Ceiling arithmetic**: if any documented buffer/scratchpad/count limit
  makes single-record coverage of the parent structure impossible, the
  records cannot be alternatives.

**Sibling trap from the same incident — a human "unrecognizable" report
against a passing automated visual check usually means stacked
coverage/presentation defects, not a decode bug.** Here three stacked at
once, each individually surviving the screenshot heuristic: the partial
coverage above; a vertical-axis sign flip (elevation stored down-positive,
PSX Y-down family — measurable from raw data alone: 74% of vertices at 0,
25% on one side reaching −642, 0.9% on the other → the 25% side is
"up"/mountains; exported raw, mountains render as trenches); and unlit
`MeshBasicMaterial` presentation (single-colour models render as flat 2D
silhouettes; placeholder `fill==0` faces render invisible black on a
near-black background). Stored winding likewise followed the PSX GPU's
Y-down screen-space front-face convention (100% of faces CW seen from
above under a Y-up reading) — GL/OBJ consumers must reverse rings; both
the axis sign and the winding convention fall out of one cross-product
normal census on the raw data, no renderer needed.
