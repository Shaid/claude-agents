# A verify-script census for "does this function reference global G" via string-matching disassembled text never finds a `lui`+load/store pair, even when the code plainly does reference G

**When it bites:** writing an automated check (inside a committed verify
script, not just eyeballing a listing) that walks a disassembled address
range looking for whether it references a specific absolute global/field
address — and implements that as `insn.text.includes(hexOf(G))` or an
equivalent substring/regex match against the disassembler's own printed
instruction text. The check reports a clean "not found" for a function you
have independent reason (a doc's own pseudocode, a sibling citation) to
believe really does touch `G`, and the negative looks decisive because
nothing in the output signals a gap.

## What's actually happening

Most from-scratch disassemblers for fixed-width RISC ISAs (MIPS, PowerPC,
ARM without literal pools) print **one instruction at a time**, and an
absolute 32-bit address is never encoded in a single instruction — it's
built from a pair: `lui $r, HI` followed by a load/store/`addiu` using
`LO($r)`. The disassembler has no obligation to fold that pair into one
resolved value in its text output; each instruction is disassembled
independently, so `lui $v0, 0x8005` and `lw $v0, -0x4780($v0)` each print
their own raw 16-bit immediate operand. Neither line's text ever contains
the string `"0x8004b880"` (the real resolved address) — only `"0x8005"` and
`"-0x4780"` do, separately. A search built to find the *resolved* value as
a literal substring of the disassembly text structurally cannot match
either line, no matter how many times the code really does reference `G`.

This is the mirror image of `lui-addiu-negative-low-half-borrows-from-high-
half.md`'s scanner variant: that lesson is about a scanner that *does*
attempt the `lui`+immediate pairing but computes the wrong high-half
candidate for one instruction form (`ori` vs `addiu`); this one is about a
scanner (or ad-hoc check) that never attempts the pairing at all, and
instead searches for a value that will never appear verbatim in either
instruction's own printed text.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`), round 201: re-verifying an already-
documented function's own pseudocode (`battle-logic.md` §30.2, "reads
`halfword[0x8004B754]`, indexes `byteTable[0x8004ABC0]`, ...") with a fresh
committed script, the first version of the check did:

```ts
if (insn.text.includes('0x4b754') || insn.text.includes('-0x4b754')) sawHit = true;
```

against every instruction in the function's address range. All six globals
the doc's pseudocode named came back "not found," despite the write
instruction two lines later (`sb $v1, 0x96($v0)`) matching byte-exact —
i.e. the function plainly *was* the right one, just apparently missing
every global reference the doc claimed. Dumping the raw disassembly by
hand showed the real instructions:

```
0x8005dea4  lui $v1, 0x8005
0x8005dea8  lh  $v1, -0x48ac($v1)   ; resolves to 0x80050000 - 0x48ac = 0x8004b754
```

Neither line's text contains `0x4b754` in any form — the check was
searching for a string that could never exist in this disassembler's
output, for any function, ever.

## The fix

Never string-match a disassembler's per-instruction text against a target
*resolved* address. Instead, walk the instruction stream, detect `lui
$r, HI`, then scan forward a small window (a handful of instructions,
stopping early if `$r` is redefined first) for the next instruction whose
text references `LO($r)` — any `lw`/`lh`/`lhu`/`lb`/`lbu`/`sb`/`sh`/`sw`/
`addiu` form — parse `HI` and `LO` out of both instructions' own operand
text, sign-extend `LO`, and compute `(HI << 16) + LO`. Collect every
resolved address the function's opening block constructs this way into a
`Set<number>`, then check membership against each expected global. This
generalizes past MIPS: any ISA that splits an absolute address across two
or more instructions (PowerPC `lis`/`addi`, ARM `movw`/`movt`, SH-2's
literal-pool-free variants) needs the identical two-step
"detect-the-high-half, pair it with the next real use, then compute" logic
before a resolved-address census can find anything at all — a plain text
search over such a disassembler's output is structurally blind to every
multi-instruction address, not just wrong on some of them.
