# A structurally-promising "extra data" field needs a corpus-wide magnitude/exact-value census before being trusted as real per-instance data

**When it bites:** a field or vertex/record found via structural reasoning
(unreferenced by any face/index list, sentinel-valued, sitting at a
suggestive position like a root/solo node) looks like it could be the
missing per-instance data a decode needs (a translation, an offset, a
scale) — and it "looks plausible" on the one or two instances you first
checked, tempting you to wire it in and move on.

**The generalizable move:** before trusting such a field as genuine
per-instance data, run two cheap corpus-wide checks:

1. **Magnitude consistency** — do the values fall in a plausible, roughly
   consistent range relative to other already-confirmed same-role
   quantities in the same record (e.g. comparable to sibling bone lengths)?
   Wildly inconsistent magnitude (sometimes tiny, sometimes many times
   larger than anything else in the same rig) is a sign the field means
   something else for at least some instances.
2. **Exact-value repetition across unrelated instances** — does the same
   *exact* value recur, byte-for-byte, across records that should have no
   reason to share it (different actors, different body proportions,
   different packages)? A single coincidental repeat is normal; the same
   exact value showing up in several structurally-unrelated instances is
   the signature of a shared per-template constant or a repurposed
   field (e.g. a weapon-socket offset, a debug marker, an unused default)
   that only *looks* like real per-instance spatial data because of where
   it sits in the record.

Either finding alone is enough to disqualify the field as trustworthy
per-instance data — document it as an open, repurposed-field-shaped lead
rather than silently wiring it into a decode or silently dropping it as
noise.

Confirmed on Parasite Eve (PSX): an unreferenced "marker" vertex (zero
face references, sentinel-looking coordinates) at root/solo bone positions
looked like a promising root-to-root translation candidate after finding it
in one model. A corpus-wide census across 417 such markers in 830 models
found both symptoms at once — inconsistent magnitude (sometimes
bone-length-scale, sometimes far larger than any real bone in the same rig)
and the identical exact value (e.g. `(8,-12,-41)`) recurring across four
unrelated actor packages with different body proportions — decisively
refuting it as real per-character spatial data. It was documented as an
open lead (a possible repurposed field, e.g. a weapon-socket offset) rather
than used in the shipped decode.
