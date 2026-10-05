# A confirmed index register/field may feed a second, parallel table at the exact same code site

**When it bites:** you've confirmed a field or register (a level/node index, a type id) as the index into one table and are about to mark that consumer done. Look just past the read for a second base-load on the same index. Also: you're treating the field's consumer list as closed. Also: the same register is compared against a small offset of an aliased struct, before writing it up as "role not confirmed".

Parallel per-index tables sharing one lookup key are a common
data-authoring pattern (one array for a stat, a sibling array for a
category/selector byte), and the second table is easy to miss because it
sits right next to bytes you've already read and marked "done."

Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`): a stage-node
index (`$34(a5)`) was already confirmed as feeding a per-node difficulty-
rank table via `lea $21b38(pc),a0 / move.b (a0,d0.w),$48(a5)`. The very
next two instructions in the same routine load a **second** base register
(`lea $21bb0(pc),a1`) and read a second byte through the identical index
(`move.b (a1,d0.w),$49(a5)`) — a previously-undocumented per-node table
whose own consumer (found separately, by searching for other readers of
the newly-read field) turned out to be a monster-spawn-table block
selector: genuine, new level/stage design data that a session which
stopped at the first table would have missed entirely.

**A free bonus once found:** the second table's length doesn't need to be
guessed or hardcoded — the byte gap between the two `lea` targets
(`secondTableBase - firstTableBase`) gives it directly when the tables are
stored back-to-back with no padding, which is easy to verify (it should
equal the first table's own already-established length, with zero
slack).

**Fix:** whenever you trace a table lookup to confirm it, read a few
instructions past the point where the read completes, looking for a
second `lea`(or equivalent base-load)/index-read pair using the *same*
index register before it's clobbered. This is cheap (you're already
disassembling that code) and the yield (finding real, undiscovered
per-index data) is disproportionate to the cost.

**A later session on the same project found a THIRD consumer, at a
completely different code site** — not caught by re-reading past the
original lookup, because it isn't nearby in the ROM at all. The index
field (`$34(a5)`) also gates real SCROLL3 background-tilemap-fill code
elsewhere in the binary, found by widening the search technique itself:
a plain absolute-address byte scan for an UNRELATED, already-confirmed
hardware register in the same subsystem (the video hardware's own
`SCROLL3_BASE` physical address, known from an earlier session's
MAME-driver-sourced work) turned up a small, tractable cluster of code
that happened to open with a `cmpi.b #imm,$34(a5)` dispatch on the exact
same index field. **Generalized fix:** a confirmed shared index/type
field's consumer list isn't bounded by "the same code site" OR "reachable
from the one function you already traced" — periodically re-scan for the
field's own byte-pattern (e.g. a `cmpi.b`/`move.b` instruction referencing
its exact `(d16,An)` displacement) across the WHOLE decrypted image
whenever a new, unrelated already-confirmed address/register in the same
subsystem gives you a fresh place to look, rather than assuming the
consumer list closed once the first one or two were found.

A third instance shows the "second parallel table" doesn't even need to
be new disassembly — it can already be sitting, fully decoded, in a
completely different project doc about a different subsystem, joined
only by a small numeric field offset. Valkyrie Profile (PSX, `valkyrie`
project): a scene-script opcode's own handler used one register both to
index a 25-slot per-object "companion array" (`record = base +
236*operand`) AND, a few instructions later in the SAME function, to
compare against 4 bytes of a persistent global struct at a small offset
(`ctx+0x39c+idx`). Recognizing the second use as worth investigating (not
just "another read of the same register, already understood") led
straight to an unrelated doc — a battle-roster-construction writeup for a
totally different overlay — whose own already-disassembled function read
`P.u8[0x39c+pos]` for `pos` 0..3 as the party-seat(0-3)->characterId array,
where `P` was already independently established (a third doc, an even
earlier round) to be the identical object as the scene-script overlay's
own `ctx`. Three separately-confirmed facts, none citing the others by
name or address, turned out to describe the same 4 bytes: this is what
named the opcode's own operand as a character id and its clearing mode as
a party-membership-change primitive, with zero new disassembly of "who
else reads this" required. **The specific technique**: when a confirmed
index/comparison register touches a struct at a small, plain-looking
offset (the kind that could easily be assumed unrelated or coincidental,
unlike a large or distinctive constant), and the struct's base pointer is
already known — even loosely, "some persistent global" — to be an alias
of another struct documented elsewhere under a different local name,
check that OTHER doc for the identical offset before writing the field's
role up as "not confirmed." The join key is the number, not a shared
label; grepping for the base pointer's usual alias name in the other doc
won't find it, because the other doc uses its own alias.
