# Field-centric bit-consumer census misses a consumer that a constant-first (mask-centric) census finds in one pass

**When it bites:** a per-bit producer/consumer census that starts from every
load of a struct field and forward-chases the loaded register through
`andi`/`ori`/reg-reg `and`/`or` has returned zero consumers for a flag across
2+ rounds, and the tool (a) redefines its tracked "live" register on every
masking use and/or (b) starts its constant tracker at the load instruction
— before writing a settled negative, run the inverse census: enumerate
every way the target constant is built (`lui r,hi`; `lui hi; ori lo`;
`addiu r,$zero,-N`), follow the constant register forward to its reg-reg
consumer, and backtrack the OTHER operand to its defining load with no
window limit and single-entry-edge (not linear) path awareness.

## What happened

Valkyrie Profile (PSX, `valkyrie`), field overlay TOC slot 2292 (base
`0x8002f824`), flag `obj+0xe8` bit 17 (`0x20000`). Its producer
(`FUN_80032668`, `0x80032880`) was known from round 6. Five rounds (6, 14,
15, 17, 18) of progressively more careful field-centric censuses — literal
`0xe8($reg)` scans, stride-modulo biased-base tracking, combined-mask/
sub-word/sign-bit extraction, store-verified reg-reg classification, a
bias-free literal fallback, per-room native-module scans — all returned
**zero** consumers, and the item was escalated to `re-oracle`. The
escalation found the consumer in one pass at `0x800318bc` (TEST) /
`0x800318d4` (one-shot CLEAR) inside `FUN_80031194`'s type-5
allowlisted-kind-3 dispatch arm. Two independent, structural blind spots,
both reproduced as negative controls in
`tools/valkyrieprofile/verify-e8-bit17-round19.ts` (88/88, both discs):

1. **Sibling-test register reuse beyond the chase window.** `lw
   $v1,0xe8($s0)` at `0x800317ec` is first tested for bit 6 via `andi
   $v0,$v1,0x40`. The chase adopts `$v0` as its live register and dies
   three instructions later when `$v0` is reloaded — but the ORIGINAL `$v1`
   stays live across a 4-way kind dispatch and is tested for bit 17 **52
   instructions later** (`lui $v0,0x2; and $v0,$v1,$v0`). Compilers keep a
   loaded flags word in a callee-saved-or-untouched register for a whole
   switch; a "redefine live on every use" chain with a 16-instruction window
   is structurally blind to every test after the first. The project's own
   round 14 had already *disclosed* exactly this limitation for a sibling
   item ("reads the same loaded register for an unrelated SIBLING bit test
   first") and never generalized it into the tool.
2. **Mask constant split around the load by delay-slot scheduling.** The
   CLEAR's `lui $v1,0xfffd` sits in a `beq` delay slot at `0x800318c4`,
   BEFORE the `lw $v0,0xe8($s0)` at `0x800318c8`; the `ori $v1,$v1,0xffff`
   comes after. A constant tracker that begins at the load sees only an
   `ori` on an unknown source and learns nothing, so the following `and
   $v0,$v0,$v1` is classified "unknown mask" and dropped — even though the
   store-back at `0x800318dc` would have confirmed it. On any ISA with
   delay slots (MIPS, SPARC, SH) or any scheduling compiler, half a mask
   constant landing before the load is routine, not exotic.

The technique that found it inverts the search direction, the same idea
as `value-construction-narrows-flooded-address-census.md` (there: an
address with too many xrefs; here: a chase with too few hits — same fix).
A bit >= 16 on MIPS can only be built through `lui` (with an optional
`ori`), and its complement only through `lui 0xffff^hi; ori 0xffff` or a
sign-extended `addiu`. Enumerating every such site overlay-wide (60 `lui
r,0x2` sites) and backtracking each reg-reg `and`/`or` partner to its
defining load yields exactly three `0xe8`-loaded operands — the TEST, the
CLEAR, the already-known SET — and classifies every other site as a
compare/divide constant or a mask on an unrelated global/struct. One pass,
no window, no bias tracking.

**Aggravating factor — the answer was already in the project's own docs,
twice.** A round-6 prose sentence described "a bit-`0x20000`-gated
clear-and-zero-velocity step" in this very dispatch without naming the
word, and a round-14 `lui 0xfffd` mask-constant census row literally
labelled this site "`e8` bit 17" while hunting a DIFFERENT field's bit 17
(`obj+0xe4`). Neither was ever cross-referenced against the open item —
`doc-self-cross-reference-before-fresh-disassembly.md`, again: grep the doc
for the bare mask constant (`0x20000`, `0xfffd`) before the next census
round, not just for the field offset.

**Smaller trap hit while verifying:** a LINEAR "last writer of register R
before address X" backtrack crosses into other, never-executed dispatch
arms — for the TEST it returned `lw $v1,-0x6a34($v1)` from the case-`0x80`
arm, not the executed path's `lw $v1,0xe8($s0)`. Fix: when the walk
reaches a block whose linear predecessor is a `j`/`jr` delay slot (no
fall-through) and which has exactly one incoming branch edge, continue from
that branch's own delay slot and source instead of the linear predecessor;
and prove the register is unwritten along the *executed* path with a
path-sensitive walk that follows the specific branch decisions.

## Fix

1. A field-centric chase must keep tracking the ORIGINAL loaded register
   (and every copy of it) until that register itself is overwritten — an
   `andi rd,rs,imm` with `rd != rs` is a TEST on `rs`, not a redefinition
   of the chain; drop the fixed instruction window in favour of
   "until overwritten or function end."
2. Seed the constant tracker from the function entry (or at least from
   N instructions before the load), not from the load itself.
3. Regardless of 1-2, before writing any "zero consumers" negative for a
   bit whose mask needs a multi-instruction build, run the constant-first
   census as an independent second technique — it is cheap, has no window,
   and is blind to neither failure mode above.
