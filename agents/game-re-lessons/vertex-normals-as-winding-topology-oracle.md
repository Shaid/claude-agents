# Per-vertex normals can double as the oracle for triangle winding when nothing else confirms it

**When it bites:** a mesh format's triangle-strip/index topology is
otherwise fully decoded (indices resolve, counts close exactly), but no
field encodes starting winding order/parity, and no bit pattern correlates
with which strips render front-face vs. back-face.

If the format also stores per-vertex normals, they're a free, independent
structural oracle for winding — even before any renderer or texture is
available. For each candidate triangle, compute its face normal from the
two candidate winding orders (`cross(v1-v0, v2-v0)` and its negation) and
compare against the *stored* vertex normals at its three corners (dot
product / sign agreement). The correct winding for that triangle is
whichever orientation agrees with the stored normals; across a real corpus
this produces a sharp bimodal split — confirmed at **100% agreement** for
the correct winding and **~50%** (i.e. no signal at all) for the wrong one,
on real Drakengard (PS2) `CSFg` mesh data. A near-100%-vs-~50% split from
this test simultaneously confirms three things at once: the topology
grammar is right (triangles are being formed from the right index groups
at all), the position decode is right (normals wouldn't agree with garbage
positions), and the normal decode/scale is right.

**A genuine possible finding, not just a technique:** this test can also
prove winding parity was **never stored at all**, rather than merely being
hard to find. On the same corpus, roughly half of all multi-triangle strips
wind one way and half wind the other, *uniformly per strip* (internal
mixed-winding strips were a rounding error, ~0.1%) — and no bit anywhere in
the file, no strip-ordinal parity, no running-vertex-count parity, and no
sub-block ordinal correlates with which. That combination (real, external
signal available via normals; zero internal signal correlating with it) is
itself evidence the original engine relied on the platform's GPU/GS doing
no backface culling at all, making stored winding a genuine non-issue for
the original renderer — not a field the format-cracking session simply
failed to locate. Don't keep searching for a parity bit once a real
external oracle (like this one) both resolves the practical need (render
correctly by deriving winding from normals) and quantitatively rules out
every internal-bit candidate tried.
