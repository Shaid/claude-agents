# An even 360/N angular fan-out of sibling branches can coincidentally re-land on an already-used direction axis — use golden-angle spacing, and blend a mirrored pair off the parent direction instead of a full perpendicular split

**When it bites:** building a heuristic (not decoded) geometric layout for a
tree/hierarchy with no real per-node direction data — e.g. assembling a
skeleton's bind pose from hierarchy + bone-length alone, laying out a
directory tree, or fanning any set of N sibling nodes around a shared parent
axis for display — and evenly spacing them at `360deg/N` (or `2*pi*i/N`
radians) around the parent's direction.

**The generalizable move:** an even angular split has small-integer
periodicity, so it can exactly coincide with a direction another part of the
same layout logic already assigned via a different rule (e.g. a
special-cased "mirror this equal-length pair to either side" branch that
runs before the generic fan). When that happens, two structurally distinct
sibling branches land on the identical direction vector — a silent, exact
anchor/position collision with no error or crash, invisible unless you
specifically census pairwise distances across the whole corpus. Prefer
**golden-angle spacing** (`angle = phase + i * PI*(3 - sqrt(5))`, i.e.
`~137.5deg` per step) for any such fan — it has no small-integer periodicity,
so it cannot coincide with a fixed reference axis (0 degrees / 180 degrees /
90 degrees) for any practical sibling count, while still spreading nodes
usefully around the circle.

A second, related trap in the same class of heuristic: when mirroring a pair
of siblings to either side of the parent's own direction (e.g. two
equal-length limb bones), a full 90-degree perpendicular split is the
"obviously symmetric" choice but is only anatomically right for *some*
attachment types (a shoulder pair splitting sideways off a spine) and wrong
for others (a hip pair splitting off a downward-pointing pelvis root — a
full sideways split flattens the pair into a non-descending "shelf" instead
of visibly descending legs). Nothing in typical hierarchy+length-only data
distinguishes which attachment type a given pair is, so **blend the split
partway toward the inherited parent direction instead of a full turn** (a
value in the 45-70 degree range from the parent axis, not 90) — it reads as
plausible for both "sideways-splitting" and "downward-splitting" cases
simultaneously, at the cost of not being exactly right for either.

Confirmed on Parasite Eve (PSX)'s heuristic bind-pose assembly
(`tools/shared/psx-actor-pose.ts`): an initial full 90-degree mirror split
looked fine for an arm pair (attached to an "up"-facing root) but flattened
a leg pair (attached to a "down"-facing second root) into a sideways,
non-descending shelf — fixed by blending the split to 60 degrees off the
parent direction. Separately, an even `2*pi*i/N` fan for N=2 leftover
unpaired siblings placed them at exactly 0/180 degrees relative to the same
basis vector an already-processed mirrored pair used, producing a real,
reproducible collision in the shipped corpus (package 294, model 1, bones
21 and 31 landed on an identical anchor) — caught only by a corpus-wide
0-collision census across all 830 models, not by inspecting any single
model by eye. Switching the leftover-sibling fan to golden-angle spacing
(with a small phase offset) eliminated all 60 corpus-wide collisions with
no other change.
