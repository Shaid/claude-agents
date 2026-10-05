# A save-file "gather" routine can write back into the live struct it's reading, not just copy it

**When it bites:** Tracing a save-file writer's gather loop (or any routine
assumed to only READ live game state and WRITE it into a save buffer) —
before treating the routine as passive, check whether any of its individual
field copies is actually a read-modify-write against the SOURCE struct
itself, not a plain load. A field's on-disk value may reflect something the
save routine computed and wrote into live memory during the save, not
whatever value was already sitting there when the player opened the menu.

## What went wrong

Valkyrie Profile (PSX, `valkyrie`): `saveGame`'s gather loop reads the live
persistent struct `P` field-by-field and copies each into the 9,060-byte
save image, exactly as expected for every other field. One field,
`P+0x3C0` (a packed config-flags byte with two already-confirmed bits — a
"Dash control" sense and a camera-override flag), is different: right
before the plain-looking `lbu ...; sb ... -> image` copy, the routine reads
a scratch byte at a fixed global address, and depending on its value either
sets or clears bit `0x80` of `P+0x3C0` **in place**, then re-reads the
now-mutated byte and saves *that*. The load side's own restore of this
field is a completely ordinary, unmasked `lbu image ; sb -> P+0x3C0` — no
special-casing there at all — so nothing about the load path hinted the
save path was anything but a plain copy too. Nobody had reason to suspect
this one field among dozens of otherwise-identical scalar copies, and the
mutation would be invisible to any check that only diffs the save-side
gather against the load-side scatter for "does every offset round-trip" (it
does — the RMW doesn't break the mirror, it just means the mirrored value
isn't the one the live struct held a moment earlier).

The scratch gate byte's own writer, once traced, turned out to be a
per-controller pad-poll call site in an unrelated menu overlay — i.e. the
save routine is quietly baking a live hardware-poll result into a
gameplay-persistent config bit every time the player saves, a real,
previously undocumented mechanic with no reason to be suspected from either
side of the save/load pair in isolation.

## The fix

When disassembling a save-gather (or any "read live state, write it out")
loop field by field, don't stop reading each field's block at the first
load instruction that feeds the eventual store — check whether the SAME
destination address the field claims to be *reading from* also appears as
a store target a few instructions earlier in the same block. A genuinely
passive copy is `load(src) -> store(dst)` with `src` never written in
between; a mutating gather is `load(src) -> compute -> store(src) ->
load(src) -> store(dst)` — the extra store-then-reload round-trip through
the source is the tell. This is cheap to catch once you're looking for it
(it's a handful of extra instructions per field, not a separate function),
but easy to miss if you assume "gather routines are readers" and skim past
individual field blocks once the first few look identical.

The general form: a save/load pair being verified as bit-for-bit
"inverse" of each other (every field the load restores matches an offset
the save wrote) is not the same claim as "the save routine never touches
live game state" — a gather loop can be a net side-effecting write to the
very struct it's snapshotting, and the load side's restore can look
completely ordinary while the save side's capture is not.
