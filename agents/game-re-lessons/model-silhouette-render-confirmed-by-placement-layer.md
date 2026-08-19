# A whole-model "recognisable render" can be produced entirely by the placement layer — with the per-vertex field decoded wrong

**When it bites:** a decoded vec3 vertex field is about to be (or already
was) "confirmed" as the position because the assembled model renders as a
recognisable object — on any format where per-part/per-node matrices place
many small vertex clouds (multi-node models, skeletal meshes, sector-based
levels); or when the sanity metrics backing the claim are mirror symmetry,
short median edges, low tri/vertex ratio, or smoothness — none of which
discriminate positions from *directions*.

Confirmed on ZOE2 (PS2, `flower`): the `.mdz` format was documented
**SOLVED** with the unit-normal field decoded as the position ("normalised
into the node's bbox") and the real position field left as an unexplained
"extra". Each node's vertices actually rendered as a bbox-scaled Gauss-map
shell — but 49 such shells, placed by the correct world-space node
matrices, still read as a convincing mech silhouette (crested head,
pauldrons, tapering legs), because the *placement* layer carried all the
shape information. Every statistical check offered as verification passed
identically for normals: exact `(-x,y,z)` mirror pairs (83.5% — normals
mirror too), short median edges (adjacent strip vertices have similar
normals), plausible tri/vertex ratio, bilateral symmetry. Two full
escalation passes then ran elaborate statistics comparing the true
position field against normals *computed from the wrong positions*,
refuting normal/tangent/color/second-position hypotheses one after
another. The VU1 microcode settled it in one pass (ITOF12 on the "position"
field = ±1.0 normal; ITOF4 + matrix multiply on the "extra" = position).

**The one-line tell that was available the whole time:** the accepted
"position" field had constant magnitude (4095..4096) for 100% of vertices.
Nobody histogrammed |v| of the *accepted* field — only the mystery field
got scrutiny.

**The general checks:**
- When a vec3 field is promoted to "position", histogram its magnitude —
  constant |v| means a direction, not a position. Cheap, decisive, and it
  applies to the field you already believe in, not just the leftover one.
- A silhouette render of a multi-part model verifies the *placement*
  transform chain plus at most the coarse per-part extent — treat it as
  confirming the node/matrix layer only, and demand a per-vertex oracle
  (real hardware/emulator geometry path, VU/GPU code trace, or
  face-normal-vs-stored-normal agreement on the candidate positions) for
  the vertex field itself.
- If a sibling field of the same record stays unexplained after multiple
  passes, re-audit the *solved* fields' evidence before running more
  statistics on the unexplained one — an inverted role assignment poisons
  every derived comparison (here: "does the extra look like a normal of
  these positions?" was unanswerable because the "positions" were the
  normals).

Related but distinct: `plausible-render-not-semantic-label.md` (a correct
pixel decode carrying a wrong semantic *label*); here the decode itself was
wrong and the render still passed. See also
`vertex-normals-as-winding-topology-oracle.md` — the same
stored-normals-vs-face-normals agreement test that arbitrates winding is
also the fast confirmation that a *position* candidate is right (median
dot jumped 0.22 → 0.93 once the fields were assigned correctly).
