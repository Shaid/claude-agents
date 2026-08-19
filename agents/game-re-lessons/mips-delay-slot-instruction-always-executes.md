# A MIPS branch's delay-slot instruction executes on BOTH the taken and not-taken path — reading it as "belongs to the not-taken branch" silently mis-derives a formula

**When it bites:** hand-deriving an arithmetic formula (a size, an offset,
a scaled index) from a disassembled MIPS function that contains a
conditional branch (`beqz`/`bnez`/`beq`/`bne`/etc.) immediately followed
by an ALU instruction that writes to a register also used after the
branch target — on PS1, PS2 (EE/IOP), PSP (Allegrex), N64, or any other
MIPS-family target this project's corpus spans.

## The trap

MIPS is classically pipelined with a **branch delay slot**: the
instruction immediately after a branch always executes, regardless of
whether the branch is taken, *before* control transfers. A disassembly
listing like:

```
lw   v0, 0x20(a0)
lw   v1, 0x28(a0)
beqz v1, 0x4aac0        ; if v1==0, skip to label
sll  a0, v0, 2          ; delay slot -- LOOKS like "the not-taken-path body"
addu v0, a0, a0         ; only runs if branch NOT taken
addu v0, v0, v1
addu a0, v0, a0
0x4aac0:
; ... uses a0 here
```

reads, at a skim, as "if `v1==0`, jump past this multiply-and-add block,
so `a0` still holds its original value at the label." That reading is
**wrong**: the delay-slot instruction (`sll a0, v0, 2`) executes on
*every* path, taken or not, because it's issued before the branch
resolves. So even on the `v1==0` (branch-taken) path, `a0` gets
overwritten to `v0*4` before control reaches the label — the "skipped"
block is only the instructions *after* the delay slot, not the delay slot
itself.

## Confirmed case

Valkyrie Profile: Lenneth (PSP), `BOOT.BIN`'s `PSPVAL1.PFS` header-to-
trailer-size function (`fcn.0004aaa4`) has exactly this shape. The
correct reading — verified by re-deriving the formula in Python and
matching it byte-exact against the real 515,420,160-byte archive file —
is:

```
a0 = (header.field28 == 0) ? header.entryCount * 4      // delay-slot multiply always applies
                             : header.entryCount * 12 + header.field28
```

A skim-level reading (treating the delay slot as conditional) would have
produced "when `field28==0`, `a0` is untouched" — silently wrong, and the
kind of error that wouldn't show up as a crash, just as a plausible-but-
incorrect trailer offset/size a few thousand bytes off from the real one
(see `game-re-lessons/self-consistent-chain-wrong-unit.md` and
`negative-from-addressing-root-not-shapes.md` for sibling "plausible but
wrong arithmetic" failure classes).

## Fix / general defense

When a disassembled MIPS function's branch immediately precedes an ALU
instruction whose destination register is read again after the branch
target, **always ask "does the delay-slot instruction run on both
paths?" before trusting an instruction-order reading of the surrounding
control flow** — the answer is yes unless the target CPU is documented as
non-delay-slot (rare in this project's corpus; PS1/PS2/PSP/N64 all use
classic MIPS I/II-family delay slots). Re-derive the formula by hand,
tracing register writes on *both* the taken and not-taken paths
separately, rather than reading top-to-bottom as if it were a non-
pipelined ISA. A cheap independent check once the formula is derived:
compute it against real file/struct bytes and require an exact match
(here, `header.dataSectorCount * 2048 + roundUp(formula_result, 2048) ==
fileSize`, 0 deviation) before trusting it in a shipped decoder.
