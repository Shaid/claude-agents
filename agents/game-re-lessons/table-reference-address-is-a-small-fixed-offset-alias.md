# A table's real reference address can be a small fixed-byte alias of its documented start, not the start itself

**When it bites:** an absolute-address or PC-relative (`LEA`/`PEA
(d16,PC)`) reference scan for a confirmed/documented table's own literal
start address returns zero hits despite the table clearly being consumed
by something (structural validation already passed — every entry
resolves to a real target — or a doc/hypothesis says it must have a
reader) — especially when the table's per-record format has an
always-zero leading or trailing sub-field.

Confirmed on Knights of the Round (CPS1, `kolbold`): a 25-entry index
array at maincpu `0x5178`, each entry `[pointer:u16][zero:u16]`, had zero
hits under both a literal 32-bit absolute scan and an `LEA`/`PEA
(d16,PC),An` PC-relative scan for `0x5178` itself. The real consumer
existed (3 real call sites), but it referenced a *third* address,
`0x5176` — exactly 2 bytes before the documented start. This wasn't a
mistranscription: because every entry is `[pointer:u16][zero:u16]`, a
**misaligned** 32-bit long read starting 2 bytes early picks up `[the
previous entry's always-zero field][this entry's pointer field]`, which
equals the entry's pointer value zero-extended into a 32-bit register.
`base = table_start - 2; movea.l (base, index*4), An` is therefore
arithmetically *identical in effect* to reading the table's own pointer
field directly at `index` — just reached through an offset base instead
of an explicit 16-bit-to-32-bit zero-extend instruction. A companion
header table in the same binary used the identical trick against a
sibling array (`0x510e = 0x5110 - 2`).

This generalizes past this one 68000 idiom: any compiled load that reads
a *wider* value than one record field, straddling a record boundary, can
turn "the field I actually want" into "byte N of a read that starts
somewhere else" whenever the neighboring field predictably zero-pads
(or otherwise has a fixed, known value) — the compiler/programmer gets a
free zero-extend without an explicit mask instruction. The resulting
reference address is a small, fixed, and load-bearing offset — not noise,
not a bug, and not the table's own documented address.

**Fix:** when a targeted reference scan (absolute-address, PC-relative,
or any addressing-mode census) for a table's own start address comes
back empty despite good reason to believe a consumer exists, don't stop
at "no reader found." Re-run the same scan against a small window of
nearby offsets (a few bytes either side of the documented start,
especially at exactly the width of one field in the record format) before
concluding the table is unreferenced. If the table's record format has a
leading or trailing all-zero (or otherwise fixed-value) sub-field, that
field's width is the first offset worth trying. This is a narrower,
address-arithmetic-specific sibling of
`negative-from-addressing-root-not-shapes.md` (whose fix is "widen the
addressing-mode shapes you search for") — here the fix is "widen the
*target addresses* you search for," because the root cause is the same:
a real, working reference can look nothing like a direct hit on the
value you assumed had to appear literally in the code.
