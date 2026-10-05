# A block-copy's destination address can be stored as ROM DATA, invisible to a literal-operand text search

**When it bites:** a literal-immediate scan for a known target-address
range (`ld de, 0xdXXX` / `move.w #imm,An` / any "register loaded with a
constant destination" pattern) paired with a nearby block-copy
instruction (`ldir`, `movem`, a byte-copy loop) has already found some
real write sites and is being treated as exhaustive for that address
range — especially right after a *second, careful* re-run across more of
the ROM/binary reproduces the exact same hit set with zero new finds,
tempting the conclusion "the rest of this range really has no static
source."

Confirmed on Black Tiger (Z80 arcade, `kolbold` project)'s palette RAM.
A 7th session's `ld de, 0xdXXX`+`ldir` grep found 3 real palette-write
sites (122/1024 color entries) and, after a careful full-corpus re-run in
an 8th session confirmed there were truly zero *more* literal hits
anywhere in the ROM, that looked like exhaustive coverage for the
technique. But enumerating every `ldir` in the corpus (not just ones
preceded by a literal `ld de,imm16`) and tracing each one's DE value back
to its real origin found a `ld hl, TABLE; ld e,[hl]; inc hl; ld d,[hl]`
idiom: the destination address is stored as **data** in a ROM table and
loaded through HL, so it never appears as literal operand text anywhere
in the disassembly — a text/regex search for the address pattern is
*structurally* blind to it, no matter how many times or how completely
it's re-run. This one idiom, once found, led to a shared "palette script"
record-list mechanism covering 774 *additional* palette entries (896/1024
total) — six times more data than the literal-operand search alone ever
could have found, because most of it was reachable only this way.

**Fix:** when a copy/store instruction's destination is suspected to
cover more ground than a literal-immediate census finds, don't just widen
or re-run that same census — instead enumerate every instance of the
*copy instruction itself* (`ldir`, `movem`, the store opcode) corpuswide,
and for each one trace its destination register backward to whichever of
these three origins actually set it: (a) a literal immediate (what the
original census already covers), (b) a value popped/moved from a
register that was itself set earlier (trace one more hop), or (c) a
`ld r,[hl]`-style read from a ROM address — i.e. the destination is DATA,
not an operand. Case (c) is the one a literal-operand search can never
find by construction, and it is common specifically for *table-driven,
state-indexed* mechanisms (one shared copy routine serving N variants
selected by an index into a pointer table) — which is exactly the shape
worth suspecting whenever an already-solved narrow range coexists with a
much larger, structurally similar but still-open range in the same
address space.
