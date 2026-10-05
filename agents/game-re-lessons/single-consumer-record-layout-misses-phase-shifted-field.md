# A record's field layout derived from one consumer can miss a field positioned before the anchor offset that consumer happens to use

**When it bites:** a data table's per-record layout (field offsets,
stride) has been pinned down by disassembling exactly *one* of its known
consumers, and the table has two or more other known call sites that
haven't been read at the instruction level yet — especially when the
table's own address is only ever accessed through a running byte-offset
register whose "zero point" was set by whichever field the first-read
consumer happened to compare first. **More generally: this also bites when
the "record layout" fact you're missing isn't a field offset at all but
the whole addressing SCHEME** — a shared table's base address being
confirmed, and even several consumers' individual value reads matching,
does not mean every consumer addresses it the same way.

## What went wrong

Valkyrie Profile (PSX, `valkyrie`): a 33-entry, 12-byte-stride static
table's record layout was described, after disassembling its first known
consumer, as "id (u16) at offset 0, flags byte at offset 2" — accurate as
far as it went, since that consumer only ever reads those two positions
relative to the loop's own running offset register. A prior pass had
found (but not disassembled) two more call sites referencing the same
table via the identical access idiom. Reading those two consumers'
bodies for the first time this session revealed each treats the record
differently: one reads offset+3 as a small selector into a caller-
supplied array; the other, on a match, reads a 4-byte value at
`(matchedRecordOffset − 4)` — i.e. **4 bytes *before* the position every
prior description called "the record's start"** — and calls it directly
as a function pointer. The record's real per-consumer-relevant span is
phase-shifted relative to the "id at offset 0" framing that a single
consumer's disassembly had locked in as the working model, and nothing
about the first consumer's own instructions could ever reveal this,
because it never reads anything before its own offset-0 anchor.

## Fix

Treat a record layout inferred from one consumer's disassembly as a
*partial* view scoped to whatever fields that specific consumer happens
to touch, not the record's full or canonically-anchored shape — even when
the count/stride facts it establishes (loop bound, byte-offset increment)
are independently solid. Before publishing a record layout as complete,
disassemble every other known call site to the same table/idiom and check
each one's own field accesses relative to the *same* running-offset
register, including negative displacements relative to the position the
first consumer treated as "offset 0." A consumer that reads before the
established anchor is not a contradiction to resolve away — it is direct
evidence the anchor itself was an arbitrary phase choice, not the
record's true structural boundary. This generalizes past this one case:
any table reached through more than one code path is a candidate for a
canonical-offset assumption that quietly encodes "wherever the first
disassembled consumer happened to start counting," not the record's
actual field 0.

## A further generalization: addressing SCHEME diversity, not just offset diversity

Confirmed on the same project, a different table (Valkyrie Profile PSX,
`valkyrie`): two shared GPU-render "template" lookup tables (a 1108-byte-
stride table and a 112-byte-stride table) are read by several
independently-compiled per-room native modules. Enumerating "every known
reader, and the value each one reads" looked like a complete model — until
a newer consumer of the 112-byte table turned out to address it via a
totally different CONVENTION from the earlier ones, not just a different
offset: earlier readers computed a byte offset into the row struct and
read a value out of it directly; this one instead used the row index as a
*word-array* index with an *additive* base, XOR'd a selector the other
readers used raw, and — the biggest departure — didn't read a value out of
the row at all, it took a *pointer into the row* and handed that pointer
to a shared rendering-primitive function, which then did its own internal
field reads. Same base address, same underlying table, three independent
axes of divergence (unit/scaling, transform-before-index, value-vs-pointer
semantics) that no amount of re-checking the *already-confirmed* readers
could have surfaced.

**Fix (generalized):** when a shared table has more than one known
consumer, don't stop at reconciling field offsets across them — check
whether each consumer treats the base address as byte-addressed vs.
element/word-addressed, whether it transforms the selector/index before
using it (XOR, scale, add a constant row base) or uses it raw, and whether
it dereferences a value at that position or forwards a *pointer* to the
position for someone else to interpret. "This table's format is solved"
should mean "every known addressing convention against it is
characterized," not "every known value read from it decodes to something
plausible" — a new consumer can pass every plausibility check on its own
output while using a structurally different access convention that
happens to still land on valid-looking data.

## A third generalization: literal displacement arithmetic can reveal several already-documented fields are the identical byte

Confirmed on the same project (Valkyrie Profile, PSX, `valkyrie`): three
scene-script opcodes were independently documented, in three separate table
rows, as touching three seemingly distinct fields of a shared 236-byte
companion record — one via `base + 236*idx − 0x13`, one via `base +
236*idx + 0xd9`, one via `(base + 0xAC) + 236*idx + 0x2D`. Nothing about any
one citation looked wrong or incomplete on its own; each was a correctly
disassembled, correctly cited displacement off its own base pointer. Only
computing the literal arithmetic (`236 − 0x13 == 0xD9`, and `0xAC + 0x2D ==
0xD9`) revealed all three are the *same* absolute byte, just phase-shifted by
each function's own choice of base register — one opcode's mode-0/1/2
dispatch and two other opcodes' read/write pair turned out to be one
coherent mechanism operating on a single shared field, not three separately-
opaque, unrelated behaviours.

**Fix, framed as a positive technique rather than a missed-field negative:**
whenever two or more already-documented fields on the *same* record/struct
have displacements that are suspiciously close in magnitude (within one
struct's stride of each other) but were found via different base pointers
in different functions, compute `base_delta + displacement_delta` for every
pair before assuming they're unrelated. A match is free, load-bearing
corroboration that unifies separately-opaque findings into one mechanism —
exactly the flip side of this file's core lesson that a record has no single
canonical "field 0," just whichever phase each consumer's own base pointer
happens to use.
