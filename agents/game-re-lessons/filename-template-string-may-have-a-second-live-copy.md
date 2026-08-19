# A filename template can exist in more than one copy — finding one consumer is not finding *the* consumer

**When it bites:** a resource is opened not by a literal filename but by a
**patched template** (`"D/PLNX"`, `"MON%02d.PIC"`, `"LEVEL_.DAT"` — a
placeholder character overwritten at runtime), you've found the template
string, resolved the pointer table that holds it, disassembled its consumer,
and you're about to write "this file is inert / dead / only read by the
bundled utility / no live consumer exists."

Also bites the moment a resource family's status is "unreferenced" while the
*game* obviously has a feature that would need it.

**A literal filename appears once. A template does not have to.** Different
subsystems that build filenames the same way each keep their own copy of the
format string, because each has its own filename-template pointer table and
the linker has no reason to merge string literals across them. A single
string xref therefore tells you *which subsystem you found*, not whether
others exist.

Confirmed on Phantasie III (Amiga, `nicodemus` project). `D/PLN1`, `D/PLN2`
and `D/PLN4` were closed across multiple sessions as inert, on evidence that
was individually correct at every step: the binary contains a `D/PLNX`
template at hunk-0 `0x7253`, reached through a filename-template pointer
table at hunk-1 `0x2656`; its consumer at hunk-0 `0x20BB4` was fully
disassembled and really is a generic opaque block reader/writer that never
inspects a content byte; and that routine really does have no callers
anywhere in the binary, because it belongs to a dead embedded
character-transfer utility. Every one of those facts held up. The conclusion
did not.

There is a **second, distinct `D/PLNX` string** at hunk-0 `0x6B4E`, sitting
in slot 20 of the *game's own* template table at hunk-1 `0x21D2`. The live
map-switch routine at hunk-0 `0x1EB1E` reads 81 or 496 bytes through it
every time the party enters a castle or the Netherworld — the three files
are the castle-interior and Netherworld map arrays, and the digit patched
into the template is literally the engine's active-map-id global.

## What to do instead

- **Search the whole binary for every occurrence of the template's bytes**,
  not the first xref. This is a `bytes.find()` loop, seconds of work. Two
  hits is the whole finding.
- **Enumerate every filename-template pointer table, not just the one your
  first string landed in.** Once you have one table's base, its shape (an
  array of pointers into the string region) is a signature you can scan for.
- **Treat overlapping-but-non-identical table contents as the tell.** Here
  the utility's table and the game's table both contain `D/SXX` and
  `D/DNGX.DAT`, at *different slots* — two tables serving the same file
  family, which is exactly what you'd expect if two subsystems each built
  their own and exactly what you would not expect if there were only one.
- If the resource plausibly backs a real game feature (a map, a level, a
  scene) and your evidence says nothing reads it, weight that mismatch
  heavily. A shipped, non-empty, structured data file with no live consumer
  is rare; a missed second consumer is common.

Related: `negative-from-addressing-root-not-shapes.md` covers negatives that
fail because the *search shape* was incomplete. This one is different and
worth checking separately — here the search shape was fine and the addressing
root was correctly resolved. The unexamined premise was that the string is
unique.
