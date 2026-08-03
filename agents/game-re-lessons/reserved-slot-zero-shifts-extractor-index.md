# A reserved/blank record 0 can silently shift a downstream extractor's index by one

**When it bites:** a new, independent byte-level decoder for a save file or
memory region disagrees by a constant offset with an existing higher-level
extractor/JSON for the same or a sibling structure — before concluding the
new decoder is wrong. **Also bites at first discovery**, not just at a later
cross-check: a `PEA <literal>(An)`/`LEA <literal>(An)` instruction loading an
array's base pointer is easy to mistake for "the array's first element is at
this literal offset" when the literal is actually the *pointer's* arithmetic
base and the real first element sits one unit past it.

Many of these RPG engines reserve slot 0 of a record array for bookkeeping,
not content — a merge mask, a "not a character" sentinel, a null entry — and
real content starts at index 1. If an earlier extractor was tuned by eye
against a known first name/string (e.g. anchoring its base offset directly
on "Colchester" or "Constantine") rather than derived from a structural
invariant, it will silently skip that reserved slot and number the *second*
true record as "index 0". Every consumer of that extractor's output then
carries the same off-by-one, invisibly, until something else needs to
correlate against the *true* engine index.

Confirmed on Spirit of Excalibur: `_aForces` (character table) was already
documented as having a reserved slot 0 (an episode-transition merge mask).
`_aLoc` (location table) turned out to have the exact same convention, but
nobody had checked — the executable-side extractor's chosen base offset
pointed straight at "Colchester" and called it index 0. This was invisible
until a fresh, assumption-free save-file decoder (built for an unrelated
question — decoding `EPISODE<n>.DAT` byte-for-byte) decoded slot 0 as blank
and slot 1 as "Colchester", contradicting the older JSON. The older JSON's
index was off by exactly one, low. This wasn't cosmetic: a scene-viewer
feature built earlier in the same session had used that JSON's index to
resolve a `SCEN` id's engine-native location number, and mislabeled every
single location by one as a result.

**The check:** when two decodes of related data disagree by a constant
offset, don't assume the newer one is buggy — dump the raw bytes immediately
*before* the older extractor's base offset, one record-stride back. If it's
mostly zero/flag bytes with no name, that's the reserved slot, and the older
extractor's "index" is the true engine index minus one.

**Corollary worth checking every time:** if one record array in a save
block is known to be per-save/per-episode customizable beyond the compiled
executable's defaults (as `_aForces` already was here), check whether
*sibling* arrays in the same save block share that customization mechanism
too, not just the one table already investigated — `_aLoc` here also turned
out to gain new entries per episode that the compiled defaults never shipped.

**Discovery-time variant, confirmed on Wizardry 6 (Amiga)'s monster
resistance array:** the doc had documented a 13-element per-damage-type
resistance array starting at record offset `+0x94`, anchored directly on a
`PEA 148(A0)` instruction (148 decimal = `0x94`) that indexes into it — a
plausible-looking base, since the array *does* decode to structurally sane
percent values there. An external oracle (a published bestiary, see
`published-walkthrough-numeric-oracle.md`) later showed the real first
element is `+0x95`; `+0x94` is a reserved, always-zero slot-zero that just
happens to be the pointer's own arithmetic base, not the array's first
logical member. Two records tested against the oracle matched 26/26 at
`+0x95` and 0/26 at `+0x94` — a clean, unambiguous resolution. The general
check: when a candidate array's base offset comes from a single `PEA`/`LEA`
literal rather than an independently-provable boundary (a count field, a
terminator, a second structural cross-reference), don't stop at "this
offset decodes to reasonable-looking data" — that's exactly the false
signal a slot-zero-shifted read produces too, since the real elements are
still all there, just one position later than assumed. Treat a raw
`PEA`/`LEA` base literal as a *pointer* value to verify, not a first-element
offset to trust outright, especially for a table with no independent length
prefix.
