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

**The same failure mode hits a plain literal-offset text grep, not just a raw
opcode-encoding census.** Confirmed on Vengeance of Excalibur (`middilgard`):
having traced the exact struct byte offset (`+43`) a bytecode-VM instruction
uses as its "current program counter" field, a `grep`-style search for every
`MOVE.B ...,43(A0)`/`43(A1)` write across the whole 75,000-line disassembly
turned up ~120 hits, ~50 with literal immediates in named gameplay functions
(`_GetItem`, `_DropItem`, `_UseItem`, `_DoCombAction`, `_FightDone`, `_Trade`,
…). None of them touch the VM's PC — every one operates on a completely
different C struct (an item/inventory-list record) that happens to place an
unrelated field at the identical small numeric offset. A bare offset number,
grepped as text, carries exactly as little provenance as a raw indexed-
addressing opcode encoding does — in both cases the fix is the same: resolve
what register/pointer is being indexed at each hit (here, what the
preceding `MOVEA.L`/argument load actually assigns to `A0`) before counting
a hit as evidence about a specific struct's field.

This is the false-*positive* face of the same shape-based-evidence failure that
produces false negatives in
`bitfield-spans-multiple-addressable-bytes.md` (a bit test you cannot find
because you searched the wrong byte) and
`narrow-opcode-form-census-false-negative.md` (a consumer you cannot find
because you searched the wrong opcode form). Raw-opcode censuses fail in both
directions, and neither direction is safe without provenance:
`negative-from-addressing-root-not-shapes.md` is the general fix.

**Doing this exhaustively over a whole census — not just spot-checking a
few hits — turns a doc's "N candidate writers, none traced" hedge into a
genuine, citable closure.** Confirmed on Black Crypt (Amiga, `crawl`):
an open item read "11 candidate `byte +0x07` writers exist... none was
traced to the object array." A full census of *every* byte-writing
instruction touching that field offset across the whole 166 KB code+data
image (not just `MOVE.B` — every form that can address an odd offset:
`ADDI.B`/`CLR.B` too) found 19 write sites; resolving every single one's
base-register provenance back to a confirmed type-filter constant (a
`MOVEQ #type,D3` argument to an already-verified type-filtered lookup
helper) or a type-specific field pattern showed all 19 belonged to *other*
record kinds, none to the one the open item asked about. Because the
provenance-resolution was applied to literally every hit rather than a
sample, the result upgrades from "still not found" to "confirmed absent" —
a real, positive finding (the feature is provably dead/unreachable code),
not just an unresolved residue. The technique doesn't change; what changes
is treating "resolve provenance for every hit" as a closure method in its
own right when the candidate count is small enough to be exhaustive.

**Base-register resolution itself can be defeated by idiom repetition
density — a bounded lookback window silently picks the wrong definition,
even when you *do* attempt provenance resolution.** Confirmed on
Valkyrie Profile (PSX, `valkyrie` project): a raw MIPS opcode census for
`sw reg, 0x570(base)` hit the exact right instruction (`sw s1, 0x570(s0)`)
on its first pass, and the base register (`s0`) really did trace back to
the function's own actor-struct parameter — but the census's automated
provenance heuristic used a "nearest preceding register-load" lookback and
mislabelled it as the shared global battle-context pointer instead,
because that function reloads the context pointer via the same `lui/lw`
idiom **252 separate times**, and `s0` itself was defined only once, in
the function's prologue, roughly 200 instructions earlier than the store
— far outside any reasonable fixed lookback window, while a `ctx`-load
idiom sat much closer by sheer repetition density. The census's negative
("no actor-relative writer found, only ctx-relative ones") was reported
as clean and confident, and only unravelled when a later escalation
re-ran the identical census and manually inspected every hit's true
register-defining instruction instead of trusting the automated
attribution. **Sharpened fix:** a lookback-window base-register heuristic
degrades specifically in functions that repeat one register-reload idiom
many times (a global-context fetch, a common base-pointer refresh) — the
repeated idiom's proximity out-competes a correct but distant one-time
definition (a function's own parameter, set once in the prologue). When a
function is known or suspected to repeat such an idiom, either widen the
lookback to the function's actual start, or verify a census's "no match"
result by re-checking a handful of hits' *true* defining instruction by
hand before trusting the negative — the same fix `nearest-preceding-
immediate-is-not-dataflow.md` gives for operand *values* applies here to
operand *identity*.

**A coarse "bit-test/bit-set op with the right immediate, near a known
field access" census has the identical failure mode when TWO different
scalar fields in the same struct happen to share the same bit VALUES —
disambiguated only by which register the masking instruction targets, not
by proximity.** Confirmed on Valkyrie Profile (PSX, `valkyrie`): a
whole-overlay scan for `andi`/`ori` with an exact immediate of `0x40`,
`0x80` or `0xc0` sitting near a confirmed `obj+0xe8` (flags word) access
flagged several real `obj+0xe8` bit-6/7 sites — but also several false
positives where the masking instruction operated on a **different
register**, one loaded a couple of instructions earlier from `obj+0xc6`
(the object's "kind" byte, already independently documented as using its
own bits 6-7 for an unrelated flag pair). Textually, `lw $v0,0xe8($s0);
lbu $v1,0xc6($s0); ori $v1,$v1,0x80` reads as "an 0x80 op right next to an
e8 access," and a census keyed on proximity-to-known-offset rather than
"which register does this instruction actually write" would misattribute
the kind-byte's bit-7 set as an e8 bit-7 set. The two fields sharing the
identical small bit-value range (`0`/`0x40`/`0x80`/`0xc0`) was not a
coincidence worth doubting on its own — plenty of independent one- or
two-bit sub-flags in a struct will overlap numerically — the only fix is
mechanical: for every census hit, read which register the `andi`/`ori`/
`and`/`or` instruction's destination (and, for a read, which register
feeds the immediately-following `lw`/`lbu`) actually is, and cross-check
it against which register was loaded from the target offset, before
counting the hit. Proximity in the instruction stream is a useful
*candidate filter*, never evidence on its own — exactly the same
register-identity discipline `indexed-operand-needs-base-provenance.md`'s
base-register case demands, just applied to bit-value literals instead of
struct-offset literals.
