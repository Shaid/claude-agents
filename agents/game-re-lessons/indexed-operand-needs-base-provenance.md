# A byte-pattern census of an indexed-addressing instruction cannot identify what it operates on

**When it bites:** you've scanned a binary for a specific instruction encoding
— `BTST #n,(An,Dn)`, `MOVE.B (An,Dn),Dm`, anything using a base register plus
index — found several byte-identical hits, and are about to report them as
multiple accesses to the same table.

An indexed-addressing instruction encodes the *offset within a record* and the
registers involved. It does **not** encode which table the base register points
at. `BTST #0,(A0,D0.L)` means "test bit 0 of the byte at `A0 + D0`" and nothing
more. Two byte-identical instructions can operate on completely unrelated data
structures.

The identity lives in the **preceding `LEA`** that loads the base register, and
is independently corroborated by the **index stride** (the record size the index
is scaled by).

Worked example (War in Middle Earth, Amiga, `middilgard` project). A census
found four byte-identical `08 30 00 00 08 00` instructions and they were
reported as four tests of the same item-inventory bit. Three were false
positives:

| Site | Preceding base | Stride | Actually tests |
|---|---|---|---|
| `0x0B06E` | `LEA -16772(A4)` = `location[0]+0x08` | ×10 | location `regionFlags` bit 8 |
| `0x0F41C` | `LEA -25094(A4)` = `entity[0]+0x10` | ×38 | **items bit 8 — the real hit** |
| `0x0F726` | `LEA -16772(A4)` = `location[0]+0x08` | ×10 | location `regionFlags` bit 8 |
| `0x10436` | `LEA -11124(A4)` = `DATA+0x548A` | ×2 | combat force-slot subordinate bit 8 |

Four identical instructions, four different data structures. The strides
corroborate the bases independently: 10 is the location table's record size, 2 is
a word array's, and only 38 is the entity stride.

**Fix:** for every hit in an indexed-addressing census, resolve the base register
back to its `LEA`/`MOVEA` and confirm the target table, then check the index
stride matches that table's record size. Two independent signals agreeing is the
bar; the instruction bytes alone are not evidence of anything. If you cannot
resolve the base, the hit is unclassified — not a match.

This is the false-*positive* face of the same shape-based-evidence failure that
produces false negatives in
`bitfield-spans-multiple-addressable-bytes.md` (a bit test you cannot find
because you searched the wrong byte) and
`narrow-opcode-form-census-false-negative.md` (a consumer you cannot find
because you searched the wrong opcode form). Raw-opcode censuses fail in both
directions, and neither direction is safe without provenance:
`negative-from-addressing-root-not-shapes.md` is the general fix.
