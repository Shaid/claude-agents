# "Does location/resource X exist on the other disc/build" needs the full id span plus a corpus-wide hash search, not a same-slot check

**When it bites:** a multi-disc, multi-region, or multi-build game has a
named resource (a room, a level, a whole area) known to live at a specific
slot/id/offset on one disc or build, and the question is whether it also
exists on a sibling disc/build — especially when an earlier pass already
checked "is slot N present on disc 2" and reported it absent. A same-slot
absence check only rules out the one placement it looked at.

## What went wrong (then how it was strengthened)

Valkyrie Profile (PSX, `valkyrie`): the bonus dungeon "Seraphic Gate" was
established to live at TOC slot 4705 on Disc 1. An earlier round checked
slot 4705 on Disc 2, found it absent, and reported "disc-1-only" — true as
far as it went, but a single-slot check can't distinguish "genuinely
absent from disc 2" from "present on disc 2, but relocated to a different
slot number" (both discs' TOC layouts aren't guaranteed to assign the same
id to the same content, and this engine's own asset id spaces are known to
shift between builds elsewhere in the project). A later round closed this
properly two ways: (1) the game's own shared, disc-independent room-name
bank was used to enumerate *every* TOC slot that maps to "Seraphic Gate" —
not just the one originally flagged — turning up a full, contiguous
105-slot span (4617-4721) that is present in full on Disc 1 and absent in
full on Disc 2, with immediate neighbor slots present on *both* discs
(ruling out "the whole late-TOC region is just missing on disc 2" as a
confound); and (2) a corpus-wide SHA1 search over every one of Disc 2's own
TOC entries was run to check whether any of Disc 1's 105 Seraphic-Gate
payloads reappear under a *different* slot number on Disc 2 — a genuine
relocation would show up as a byte-identical hit at an unrelated id, which
this search came back completely negative for.

## Fix

For any "does resource X exist on the sibling disc/build/region" question:

1. **Find the resource's full extent via any available name/index bank**,
   not just the one slot/id a prior pass happened to check — a named
   in-game location is very rarely exactly one file/slot; check the whole
   span the game's own lookup mechanism assigns to it.
2. **Check presence of that full span, under the SAME id, on the sibling
   disc/build.** This alone is what the earlier, weaker pass did.
3. **Run a corpus-wide content-hash (SHA1/similar) search across the
   sibling disc/build's ENTIRE catalog** for every payload in the source
   span, to rule out relocation under a different id — not just absence
   under the same one. A same-id check and a hash search are structurally
   blind to different failure modes (renumbering vs. genuine removal); only
   agreement between both is a real "confirmed absent, not just
   unaddressed" verdict.
4. **Use immediate neighbor slots on the sibling disc/build as a control**
   — if slots just outside the target span are present on both, that rules
   out a confound like "this whole TOC region is truncated/missing," which
   would otherwise make a targeted absence look more specific than it is.

This generalizes past PSX TOC slots to any id-addressed multi-build
corpus: a save-format id space that shifts between game revisions, a
per-region archive with region-specific slot renumbering, or a patch layer
that moves content to a new key. The underlying principle is the same one
`content-type-absence-needs-multiple-independent-angles.md` uses for
whole content-*category* existence questions, applied instead to a single
named resource's existence across sibling data sets — checking one
placement and declaring the resource "not there" needs a relocation search
before it's a real negative, not a hasty one.
