# IRA label name is not a literal address

**When it bites:** About to compute an address, an offset, or an
array-entry stride by doing arithmetic directly on two IRA `LAB_XXXX`/
`SUB_XXXX`/`DAT_XXXX` label names' numeric suffixes, instead of reading
each one's own address from its definition-line comment or a hex-byte
dump next to a reference to it.

## What went wrong

IRA's auto-generated `LAB_XXXX` label names look like hex-encoded
addresses (`LAB_196A`, `LAB_1982`, ...), and it's tempting to treat the
suffix as the real embedded/runtime address — especially since IRA
*does* often name labels after something address-shaped. It doesn't:
these are sequentially-assigned symbol names, and the hex suffix has no
guaranteed arithmetic relationship to where the label actually lives.

On a Midwinter 2 (Amiga) session, this assumption was made silently: a
`MOVEA.L LAB_196D,A0` instruction was read as "the source operand is at
address `0x196D`", and a whole array-entry-spacing theory was built by
subtracting label suffixes pairwise (`LAB_1982 - LAB_196A = 0x18` =>
"24-byte spacing"). The theory was internally consistent enough to look
plausible, and wrong. Reading the RAW HEX BYTE comment for that same
`MOVEA.L` instruction showed the real embedded operand was
`0x0003DC52` — nowhere near `0x196D`.

## The fix

Never infer a label's address from its own name. Get it from one of two
places instead, both of which IRA actually populates correctly:

1. **The raw hex-byte comment column** next to any instruction that
   references the label, e.g. `;1b2f4: 20790003dc52` decodes (as a
   68000 `MOVEA.L $addr,A0` opcode+operand) to the real absolute address
   `0x0003DC52`.
2. **The label's own definition line**, which carries its real address
   as a comment, e.g. `LAB_196A: DS.L 1 ;3dc46` — the real address is
   `0x3dc46`, not `0x196a`.

Once addresses are read from real bytes rather than guessed from label
suffixes, spacing/stride derivations built on top of them (e.g. "this is
a 4-byte-apart pointer array, 24 entries long, with the first 14 being a
resolved header-offset table") become straightforward and verifiable —
confirmed self-consistent against every downstream consumer trace in
that session once corrected.

This generalizes past IRA: any disassembler/decompiler whose
auto-generated symbol names are derived from (or merely resemble) an
address should be treated the same way — the name is a label, not a
value. Ghidra's default `FUN_XXXXXXXX`/`DAT_XXXXXXXX` naming happens to
be trustworthy (the suffix genuinely is the address), which is precisely
what makes IRA's superficially-similar-looking but NOT address-derived
`LAB_XXXX` convention an easy trap for anyone used to Ghidra's.

**Corollary: two independent IRA runs on the identical binary don't share
label numbering either — even the *same* label name can name two
different functions.** IRA's default (`-LABEL=0`) numbering is assigned in
branch-target *discovery order* during that specific analysis pass, which
depends on the `.cnf`'s declared code/data ranges and preprocessing flags.
Two separately-generated `.asm` files for the *same executable* — this
project's own IRA output vs. a different project's/community's own
separate IRA disassembly of the identical binary — will almost always
number their labels differently from the first branch onward. Confirmed
on Dune (Amiga, `wyrm`): a community disassembly (`~/Development/Dune`)
named `LAB_06A5` (their run, real address `$0DD96`, cross-checked against
their own `label_map.txt`) as "the ornithopter click handler." This
project's own independently-generated `dune.asm` also has a `LAB_06A5` —
a completely unrelated `BTST #4,19(A1)` object-flag helper with no
connection to ornithopters at all. Don't treat a `LAB_XXXX` name as a
cross-disassembly identifier of *any* kind, real address or not — even
for the exact same file.

**Fix:** locate the target independently in your own project's `.asm` by
structural signature instead of by a borrowed label name — e.g. if you
know a generic dispatch/loader routine's calling convention (a small
immediate argument in a fixed register right before the call) and the
specific argument values of interest, a plain backward-scan over every
call site of that already-confirmed loader for an immediately-preceding
immediate load is a cheap, disassembler-agnostic way to find every
consumer, without needing xref tooling or any external label mapping at
all. This is what actually located the ornithopter-related code in the
case above (see `docs/dune/amiga/ornithopter.md`'s "Paths tried" table) —
cross-project label matching was tried first and refuted outright.
