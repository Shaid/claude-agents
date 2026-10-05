# A literal-absolute-address census undercounts a buffer's real accessors when sibling buffers are colocated and code reaches it via a different buffer's base register

**When it bites:** several same-size buffers/arrays sit at fixed, closely-
spaced absolute addresses (a heightfield, a parallel type/flag array, a
parallel mask array — anything using identical per-cell indexing), a
literal-address grep for one buffer's base (`lea.l $ADDR,An` / raw 4-byte
immediate scan) returns only a handful of hits, and you're about to
conclude that's the complete list of code touching it.

Powermonger (Amiga, `RUN_PROG`): a corpus-wide search for the raw 4-byte
literal `$6B943` (a confirmed exclusion-mask buffer's base address) found
exactly 3 hits — the two routines already known to read it, plus one more.
But a follow-up capstone census for the *displacement* `$2041`/`-$2041`
combined with `bset.b`/`bclr.b`/`btst.b` (regardless of base register)
found **41 hits**, because most of the real accessors never load `$6B943`
directly — they already have a *different*, sibling buffer's base
(`$69902`, a "terrain type" array sitting exactly `$2041` bytes after the
mask buffer) loaded in a register for other reasons, and reach the mask
byte via `+$2041(a0)` off that base instead. A literal-address search is
blind to this: the address `$6B943` never appears as a 4-byte immediate at
any of those 41 sites, only as an arithmetic *offset relative to a
different literal*.

**Fix:** once you've confirmed even one buffer in a same-stride "family"
(same per-cell indexing, addresses a small, related distance apart), don't
trust a literal-address census as the accessor list for any of them.
Compute every pairwise byte delta between the family's known bases, then
census the whole binary for those **displacement values** in indexed/
based-addressing instructions (any base register, not just the one you
started from) — this is the only way to find code that reaches a buffer
"through" a sibling's already-loaded base. This is the address-census
analogue of `indexed-operand-needs-base-provenance.md` (which is about a
census finding too many ambiguous hits); here the failure runs the other
way — a clean, unambiguous literal-address census finds too *few*, because
most real accesses never construct that literal at all.
