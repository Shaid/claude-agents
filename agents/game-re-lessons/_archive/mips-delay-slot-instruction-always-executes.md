# A MIPS branch's delay-slot instruction executes on BOTH the taken and not-taken path — reading it as "belongs to the not-taken branch" silently mis-derives a formula

**When it bites:** hand-deriving an arithmetic formula (a size, an offset,
a scaled index) from a disassembled MIPS function that contains a
conditional branch (`beqz`/`bnez`/`beq`/`bne`/etc.) immediately followed
by an ALU instruction that writes to a register also used after the
branch target — on PS1, PS2 (EE/IOP), PSP (Allegrex), N64, or any other
MIPS-family target this project's corpus spans. Also fires when that
register is `$v0` and the branch is a **loop-exit test** (`slti`/`sltiu`
feeding a `beq`/`bne` to the function's own epilogue) — a delay slot right
there overwrites the function's *return value*, so "what does this
function return" needs the same both-paths trace, not just "what does
this formula's operand end up as."

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

## Second manifestation (2026-09-17, `valkyrie`, VP1 PSX): the *citation* form

The same trap bites a second, less obvious way — not in reading a formula's
semantics, but in **naming the address of a store you have correctly
identified**. Valkyrie Profile's item module ends its Combo Potion handler:

```
0x8009a8f8  24420002   addiu $v0,$v0,2
0x8009a8fc  03e00008   jr    $ra
0x8009a900  a0820653   sb    $v0,0x653($a0)     <- delay slot
```

A session that had correctly decoded the handler's *behaviour* (stamp
`turn + 2` into `unit+0x653`) nevertheless wrote the writer's address as
`0x8009a8fc` — the `jr` — in five places: two doc sections, a `TODO.md`
row, and two engine source comments. The slip is invisible to every check
that mattered: the behaviour is right, the byte offset is right, the
corpus tests pass, and the address is only four bytes off and still
inside the right function. It surfaced only because a final
"re-verify the load-bearing claim straight off the disc" probe hardcoded
the cited address and printed `MISMATCH` — decoding `03e00008` as
`op=0x0, rs=31, imm=0x8`.

Why it happens: a handler's *last* instruction is visually the `jr`, and
the store looks like a trailing extra. In a delay-slot ISA the real final
store routinely sits **after** the return instruction, so "the last thing
this function does" and "the last address in this function" name
different words.

**Defense.** When citing a specific instruction address in a doc,
`TODO.md` row, or code comment — especially the one instruction a whole
correction/overturn hangs on — re-read the raw word at that exact address
and decode its opcode field before writing it down. Cheapest durable form:
make the citation an assertion in a real-corpus test
(`expect(word(0x8009a8fc)).toBe(0x03e00008)` alongside the store's own
`op/rs/rt/imm`), so the address stays machine-checked rather than resting
on prose. A prose citation nobody can re-run is exactly where a four-byte
error survives indefinitely.

## Third manifestation (2026-09-18, `valkyrie`, VP1 PSX): the delay slot decides a loop's own accept/continue direction

A third, easy-to-miss shape: the delay slot's side effect can be what a
**loop's own control flow relies on for both outcomes**, not just an
ordinary formula operand. Valkyrie Profile's ground/slope solver
(`FUN_8003506c`) walks a broadphase primitive list, and its per-primitive
acceptance test ends:

```
80035268  0051102a  slt  $v0,$v0,$s1     ; v0_old = (surfaceY < queryTop)
8003526c  10400083  beq  $v0,$zero,0x8003547c   ; branch on v0_old
80035270  01001021  addu $v0,$t0,$zero          ; delay slot: v0 := current primitive ptr
80035274  25080024  addiu $t0,$t0,0x24          ; fall-through: advance to next primitive
```

A first read sees "if the surface fails the top-of-box test, jump to
`0x8003547c`" and reasonably guesses that address is a reject/failure exit,
with the fall-through (`0x80035274`, advance to the next primitive) as the
accept path — exactly backwards. The delay slot (`addu $v0,$t0,$zero`)
*always* runs, on both the taken and not-taken paths, and it is what makes
`0x8003547c` (which turns out to be the function's own single epilogue)
return the *current* primitive as the found candidate — so branch-taken
here is ACCEPT, and falling through to advance the loop index is REJECT
(continue scanning). The condition itself reads correctly
("is the surface's Y inside the query box's range") once you separate "what
decides whether to branch" (the pre-delay-slot `v0_old`) from "what value
survives past the branch" (the delay-slot's `v0`) — but skimming top-to-bottom
conflates them and gets the loop's own accept/reject sense backwards.

**Defense, generalized:** when a MIPS loop's per-iteration test ends in a
branch whose delay slot writes the same register the loop returns/uses
afterward, don't infer "branch target = reject, fall-through = continue" (or
vice versa) from which side looks like "the normal path." Trace what each
of the two destinations (branch target and fall-through) actually *does*
next — does it reach the function's return with the delay-slot value
intact, or does it re-enter the loop head — and let that decide the
semantics, independent of which side's code came first in the listing.

## Fourth manifestation (2026-09-19, `valkyrie`, VP1 PSX): walking forward from `jr $ra` to guess the next function's start

A fourth shape, at the call-graph level rather than inside one function's
control flow: naively walking forward from a `jr $ra` (or any unconditional
jump/branch) to find "where the next function starts" gets the boundary
wrong by exactly one instruction, because the word immediately after is
that jump's own delay slot — still part of the *returning* function, not
the first instruction of whatever comes next.

```
80047400  ...
80047404  03e00008   jr    $ra
80047408  ...                    <- delay slot, STILL part of this function
8004740c  ...                    <- the real next function actually starts here
```

A session hunting for a field engine's own per-frame dispatcher made this
exact mistake twice in a row, at two different call-graph levels in the
same investigation: once treating `0x80047408` as a fresh function entry
(the real one is `0x8004740c`), and again one level up treating
`0x80046f88` as a fresh function entry (the real one is `0x80046f8c`). Both
were caught only by noticing the "function" a naive walk had produced
disassembled as a `nop`/junk-looking single instruction rather than a
plausible prologue — a shape that should itself be a tell.

**Defense:** never treat "the byte right after a `jr`/unconditional
jump/branch" as a function boundary by position alone. Confirm the
*previous* function's real end includes its delay slot (so the boundary is
`jr_address + 8`, not `jr_address + 4`), and independently corroborate a
guessed function start with a real caller (a `jal`/direct-call operand
pointing at it) rather than trusting linear adjacency to the last
instruction you decoded.

## Fifth manifestation (2026-09-27, `valkyrie`, VP1 PSX): positional word-indexing in a verify SCRIPT, not a hand-trace

The same root cause — delay slots (and interspersed `nop`s generally)
throwing off a naive "count N words from address A" walk — bites the
*tooling* too, not just manual disassembly reading. A round-202 verify
script (`tools/valkyrieprofile/verify-aoe-splash-damage-fcn800720a8.ts`)
first read a block of instructions via `const [w0, w1, w2, ...] =
words(overlay, baseAddr, n)` — destructuring a decoded word window by
*position* — then wrote checks like "the 6th word after this address is
the multiplier's `sra`." Miscounting how many `nop`s/delay-slot fillers
sit between the anchor and the target instruction produced ~13 spurious
`[FAIL]` results against bytes that were, on independent re-disassembly,
completely correct.

**Fix:** don't key a verify check by position within a decoded window at
all. Add an exact-address accessor (`wordAt(overlay, addr): number`,
reading the single word at that literal address with no counting) and
write every check against an address copied directly from your own
disassembly transcript. This sidesteps the whole class of off-by-N
counting error a MIPS delay-slot ISA invites, and is a strictly stronger
verification anyway — a check keyed by exact address stays correct even
if a later edit reorders or inserts instructions elsewhere in the same
listing, where a positional index silently shifts.

## Sixth manifestation (2026-09-27, `valkyrie`, VP1 PSX): the overwritten register is the function's own return value, in a loop-exit test

A sixth shape combines the second manifestation's stakes (silently wrong,
not a crash) with the third's mechanism (a loop-exit branch), but the
register the delay slot clobbers is `$v0` at the function's *own* `jr $ra`
— i.e. the function's return value, not a formula operand or a loop's
accept/reject sense. `func_0x80013DD0` (a resident pad-poll routine) has a
4-iteration loop bounded by:

```
80013e38  slti $v0,$t0,0x4          ; v0 = (t0 < 4)   -- loop-continue test
80013e3c  beq  $v0,$zero,0x80013f24 ; branch to the SOLE jr $ra when t0==4 (loop done)
80013e40  addiu $v0,$zero,0x1       ; delay slot -- ALWAYS executes, on BOTH outcomes
... (loop body, re-enters at 0x80013e38) ...
80013f24  jr $ra                    ; v0 is whatever the delay slot last set, NOT the slti result
```

A hand-trace read this as "the branch to the return point only fires when
`v0==0` (from `slti`), so `$v0` is `0` at every return" — reasoning that
felt airtight because it correctly identified *why* the branch fires, but
never asked whether the very next instruction (the delay slot,
unconditionally setting `$v0=1`) survives to the `jr $ra`. It does, on
**every** pass through this code, taken or not — so the function's real
return value is `1` on the "loop ran to completion" path, and `0` only on
a completely different, earlier `j`-based (not `beq`-based) early-exit
path that explicitly zeroes `$v0` before an *unconditional* jump (whose
delay slot doesn't touch `$v0` at all). The bug was caught, not by a
sharper hand-re-read, but by building a small scoped MIPS interpreter
that executed the function's actual bytes end to end (see
`hand-traced-byte-shuffle-needs-independent-resimulation.md`'s matching
manifestation) — it returned `1`, contradicting the hand-trace, and a
step-by-step trace of the interpreter's own execution pinpointed exactly
this delay slot as the divergence point.

**Defense, generalized once more:** a "does this branch's delay slot
matter" check must be applied to a function's *own* return register at
its *own* return point just as rigorously as to any other operand — a
loop-exit test feeding straight into `jr $ra` is not exempt just because
the loop's condition itself was read correctly. When a delay-slot-heavy
function's control flow has more than one or two branches feeding the
same exit, don't stop at a careful hand-trace: build the tiny interpreter
and run it.
