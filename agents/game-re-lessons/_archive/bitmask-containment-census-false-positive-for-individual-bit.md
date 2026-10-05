# A bitwise-containment test (`imm & mask === mask`) can't distinguish "this instruction touches exactly bit N" from "this instruction's immediate happens to be a superset that includes bit N for an unrelated reason"

**When it bites:** censusing a flags/bitfield word for whether one specific
bit is individually tested, set, or cleared anywhere in a binary, when
either (a) a WIDER, already-known combined mask covering that bit also
exists in the same code (a multi-bit exclusion test, a "clear this whole
group" idiom), or (b) the census accepts a register whose tracked constant
was built for an unrelated purpose (a near-all-ones AND-clear mask reused
elsewhere to isolate a *different* bit). Both shapes make a naive
containment check (`(imm & mask) === mask`) report a false "individual
bit" hit for a bit that, on closer reading, has no individual evidence at
all.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`): hunting for individual
SET/CLEAR/TEST sites of `obj+0xe4` bits 5 and 7, after already confirming
sibling bits 4 and 6 have real, distinct individual sites. Two already-known
combined exclusion masks exist on the same field — `0xf0` (bits 4-7) and
`0x2f0` (bits 4-7 plus bit 9) — used at three unrelated collision-dispatch
gates. A first-pass census (`andi $rt,$rs,imm` with `(imm & mask) === mask`)
reported "hits" for bits 5 and 7 at exactly those three combined-mask
addresses, because `0xf0 & 0x20 === 0x20` and `0xf0 & 0x80 === 0x80` are
trivially true — the census couldn't tell "this `andi` tests bit 5 alone"
from "this `andi` tests a 4-bit group that happens to include bit 5." Only
after explicitly excluding the two known group-mask immediate VALUES
(`0xf0`, `0x2f0`) from the "individual" bucket did the true, much smaller
picture emerge: bits 4/6 kept real individual hits, bits 5/7 dropped to
zero — the correct, verified answer (bits 5/7 turned out to have no
individual producer/consumer anywhere in the 369 KB overlay, only ever
appearing inside the two combined masks).

The same root cause bit a second, register-level census in the same
session: tracking `or $rd,$rs,$rt` where one operand was a small constant
built via a prior `addiu $r,$zero,imm`, looking for a register-built SET of
bits 5/7. A near-all-ones constant (`0xfffffffd`, an AND-clear mask built
elsewhere in the SAME instruction to clear a totally unrelated bit 1)
trivially satisfies `(0xfffffffd & 0x20) === 0x20` and `(0xfffffffd & 0x80)
=== 0x80` for literally any small mask — the containment test can't
distinguish "a real flag-combination constant that happens to include your
bit" from "an almost-fully-set constant that touches your bit by sheer
density." Manual disassembly confirmed the flagged instruction had nothing
to do with bits 4-7 at all.

## Fix

1. **When hunting for evidence a bit is set/cleared/tested INDIVIDUALLY,
   exclude every already-known wider group-mask immediate value from the
   "individual" bucket explicitly**, rather than relying on a bare
   containment test. If group masks aren't all known yet, sort candidate
   immediates by population count and treat any wide/dense one skeptically
   until manually checked — don't count it as single-bit evidence.
2. **For a "does anything clear ONLY this bit" question, require the
   complement to match EXACTLY** (`(~mask32) >>> 0 === targetMask`), not
   just contain it (`(zeroBits & targetMask) === targetMask`). The
   containment form is right for the different question "does anything
   clear this bit AT ALL, possibly among others" — conflating the two
   questions is what let the false positives through here.
3. **When accepting a register as "holds a real flag/set-mask constant"**
   (for a register-register `or`/`and` census), sanity-check the tracked
   immediate's own popcount before trusting a containment match against
   it — a real flag constant is small and sparse (one bit, or a handful of
   named flags); a near-all-ones or near-all-zero constant built for an
   unrelated AND-clear/OR-set elsewhere in the same function is not
   evidence about your target bit just because it happens to contain it.
4. **Always run bits you already know the true answer for (positive AND
   negative) through the exact same census as your unknowns**, in the same
   pass. Here, bits 4/6 (real, already partially confirmed via full manual
   disassembly) served as the positive control that caught the false
   "hits" on 5/7 as soon as raw counts were compared side by side — the
   asymmetry (5/7 matching only at addresses already known to be
   group-mask sites, never anywhere new) was the tell.

This generalizes past MIPS `andi`/`ori`: any bitwise-containment-based
census (ARM `AND`/`ORR`/`TST` immediates, 68k `ANDI`/`ORI`, a hand-rolled
symbolic tracker) is vulnerable the moment the target field has more than
one meaningful mask width in play (a per-bit test alongside a per-group
exclusion test, or a per-bit clear alongside a whole-struct zero-init).
Related but distinct: `struct-field-scan-blind-to-biased-base-pointer.md`
(a *true* negative hidden by addressing, not a *false* positive from mask
containment) and `sparse-table-creates-spurious-multibyte-field.md` (a
different false-positive mechanism, adjacency rather than containment).

## Third false-positive shape: an EXACT mask match against a callee's return value, not the field itself

Confirmed on Valkyrie Profile (PSX, `valkyrie`, round 10 of the same
`obj+0xe4`/`obj+0xe8` investigation): this one isn't even a *containment*
bug — the mask matched EXACTLY, `andi $reg, $v0, 0x4` with `$v0` genuinely
equal to `4`. The bug is **provenance**: `$v0` was the return value of
`jal FUN_8002fee4` (the project's own confirmed per-frame collision
resolver, which internally reads and writes `obj+0xe8`), not a fresh
`lw $v0, 0xe8($reg)`. A dataflow census that treats "any register the
callee could plausibly have derived from the field" as equivalent to "a
literal load of the field" found five sites shaped `jal FUN_8002fee4; andi
$reg,$v0,0x4` and flagged them all as bit-2 tests. Disassembling the
callee's own epilogue showed its return value is a **locally-built status
code** (values 0/1/2/3/4, optionally `+8`) encoding the just-processed
actor's OWN velocity sign that frame — status **4** happens to mean
"exactly at rest" — OR'd with an unrelated slaved-actor-candidate index in
its high bits. The numeric coincidence (status code 4 == bit mask `0x4`)
is what made it look like a struct-field test; it has nothing to do with
`obj+0xe8`. Two literal `lw $v0,0xe8($reg); andi $v0,$v0,4` sites (real,
independently confirmed) existed in the SAME function alongside these five
false ones, so a positive control alone wouldn't have caught this — the
true and false hits look identical downstream of the load/call, differing
only in what feeds the tested register upstream.

**Fix, on top of the four above**: before accepting `andi $reg, $srcReg,
mask` as evidence about a struct field, verify `$srcReg`'s **provenance**
all the way to its root. If the root is `jal <callee>` rather than a
literal `lw`/`lb`/`lh` of the field's own address, the census must not
credit it *until the callee's own return-value construction (its epilogue,
every path that sets the return register) has been read and shown to
actually forward or mirror the field* — a function that merely reads or
writes the field internally does not thereby return it. This is a sharper
version of fix #3 above (don't trust a register just because a value lands
in it): here the register's value is real and exactly matches, but its
*meaning* is completely unrelated. Treat `jal`-sourced registers as a
class deserving the same skepticism as the near-all-ones/near-all-zero
constants in fix #3, not as pass-throughs for whatever the callee touched.

## Fourth false-positive shape: a plain TEST-then-branch counted as a SET/CLEAR (no store-back required)

Confirmed on Valkyrie Profile (PSX, `valkyrie`, round 16 of the
`vp1psx-scene-script-opcodes` campaign): a "does this global ever get bit N
set or cleared anywhere" census matched `andi $rt,$rs,imm`/`ori $rt,$rs,imm`
near a load of the target word and, on that basis alone, reported the bit as
touched. This double-counted plain **TEST-then-branch** sequences
(`andi $v0,$v0,MASK; beq/bne $v0,$zero,target`, with no further use of the
result) as if they were real producers — an `andi`/`ori` only actually
*modifies* the field if its destination register is subsequently **stored
back** to the field's own address; if the next thing that happens to it is a
branch, it was only ever tested, not written. The same bug also inherited
false positive #2's shape in reverse: a large-popcount `andi` mask (a
"clear one specific bit, keep the rest" idiom, e.g. `0xfffe` clearing only
bit 0) numerically contains every OTHER bit trivially, so an ungated
containment check flagged bits it never touches at all.

**Fix, on top of the three above:** a producer (SET/CLEAR) census must
require, after finding a matching `andi`/`ori` on the tracked register,
that the modified register is written back to the field's own address by a
subsequent store (`sh`/`sw`/`sb`, same effective address) within a short
window — not merely followed by anything. And for the mask itself: compute
`popcount(imm)`; if small, treat `imm` directly as the touched bit-set (a
SET/TEST mask); if large (a "keep-most" `andi`), take the **complement**
(`~imm` truncated to the field's width) as the touched bit-set instead —
same fix as false-positive #2's exact-complement rule, restated here
because a naive re-implementation of "does this immediate contain bit N"
recreates both bugs independently unless both checks are present together.
A cheap way to catch this class of bug during development: run the census
against a bit you've already hand-confirmed has ONLY a test site and no
producer at all (a genuine settled negative) — if the census reports a
"producer" for it, the store-back check is missing.
