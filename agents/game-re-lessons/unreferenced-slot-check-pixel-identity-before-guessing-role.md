# An unreferenced table slot's role is a byte-identity check away — don't narrate a guess

**When it bites:** a sprite/icon/tile table has more slots than the
dispatch/consumer code actually reaches (a census of the table's real
consumers comes up short of its declared count), and the temptation is to
write a plausible-sounding narrative for the leftover slot's purpose
("probably a cursor/marker icon", "likely a UI element drawn elsewhere")
without having traced any code that draws it.

Confirmed on Phantasie III (Amiga, `nicodemus` project): `Dng.csh`'s
9-icon dungeon-tile bank has a cell-code dispatcher (`LAB_1388`) that only
ever selects 6 of the 9 icon-table slots. The two others adjacent to
dispatched slots were first written up as "`0x2D` — reserved, only used
as a clamp floor" and "`0x35` — never referenced by the maze walker at
all; plausibly a 'player position' cursor icon drawn elsewhere, not
traced" — a specific, confident-sounding guess with no supporting
evidence beyond narrative plausibility. A direct pixel comparison of the
decoded icon content (a five-line probe script, no new disassembly)
showed `0x2D` is byte-for-byte identical to `0x34` (a *dispatched* slot,
`stairsExit`'s own icon) and `0x35` is byte-for-byte identical to `0x2E`
(`wall`). Both "mystery" slots are simply duplicate copies of already-
understood icons, not distinct assets with an undiscovered role — the
"cursor icon" narrative was flatly wrong, and would have shipped into a
doc's "open questions" section as a specific but baseless hypothesis if
the comparison hadn't been run.

**The fix:** before writing any semantic guess for an unreferenced or
under-referenced table/array slot, diff its raw content (bytes, decoded
pixels, whatever the table's payload is) against every *referenced*
sibling slot in the same table. This costs one loop over already-decoded
data, no new tracing — and produces one of two outcomes, both strictly
better than a guess: an exact match (it's a duplicate/reused slot, role
already known — the common case for small "packed together, sequentially
indexed" asset tables authored by the same tool pass), or a genuine
mismatch (still open, but now honestly labelled "content differs from
every dispatched slot, role not traced" rather than a specific invented
story). This generalizes past icon tables to any indexed asset/constant
array where dispatch code doesn't reach every slot: string tables,
palette slots, sound-effect banks, animation-frame arrays.
