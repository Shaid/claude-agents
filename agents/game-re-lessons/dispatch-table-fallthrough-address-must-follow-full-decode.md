# Dispatch-table "no match" fallthrough address must be captured after decoding the whole table, not before

**When it bites:** writing (or porting) a decoder for any variable-length
jump/dispatch table (a `switch`-style bytecode instruction, a case table, an
indexed branch table) where the instruction format is `[selector-expr]
[count][entry]*[entry]` and "no entry matched" falls through to the address
immediately *after* the whole table. A downstream interpreter following that
fallthrough address lands mid-table (reading raw entry bytes as if they were
instructions/data) instead of past it, producing a decode error or garbage a
few steps later — often at an address that looks unrelated to the table
itself, misleading the debugging effort toward the wrong function.

## What happened

Porting a Silmarils "ALIS" VM's `cswitch1`/`cswitch2` dispatch opcodes
(Ishar, Amiga AGA) to a from-scratch TypeScript decoder: the natural way to
write the decode loop is to capture `cursor.pc` as the "no-match" fallthrough
target *before* the per-entry decode loop, then loop `count+1` times reading
`[value, relativeOffset]` pairs. That's wrong — at the moment of capture,
`cursor.pc` points at the START of the entry array (raw data bytes), not
past it. The bug was invisible in isolation (the decoder didn't crash — it
just produced a plausible-looking but wrong number) and only surfaced two
layers downstream: a scoped bytecode *interpreter* built on top of the
disassembler followed the bogus fallthrough address and threw "bad opername
token" trying to decode what was actually the table's own raw entry bytes as
if they were the next instruction. It also silently explained 3 addresses a
static CFG walk had separately flagged as "missing" compared to a
hand-verified reference disassembly — those were exactly the table-interior
addresses the buggy fallthrough was pointing computed *from*, before the
real end was known.

**The fix:** decode every entry into a local array first (advancing the
cursor through the whole table), and only *then* capture the now-correct
post-table cursor position as the fallthrough/default address. Order of
operations matters: compute the entries, THEN the "past the table" address —
never the reverse, even though capturing early looks more natural when
writing the loop.

**Generalizes to:** any decoder for a self-describing variable-length table
with a trailing/implicit "else" target — not specific to ALIS, 68000, or
even bytecode. The same mistake is easy to make in x86/ARM jump-table
decoders, protocol dispatch tables, or any format where "if you don't match
anything, keep going right after this table."
