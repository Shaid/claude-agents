# A hand-rolled constant tracker silently reports wrong masks unless it invalidates on unmodelled ops and follows tags through sign-extension pairs

**When it bites:** you are writing a raw-instruction scanner that tracks
immediate constants through registers (`lui`/`ori`/`addiu`/`xori`, or
`mov`/`movt`/`orr`) in order to attribute a store, a mask, or a table column
to a particular value — a mask census, a column map, a "which constant does
this `sw` write" sweep. The scan completes, reports plausible numbers, and
nothing flags that any of them are fabricated.

Three failure modes, all silent:

1. **Stale tracked constants.** A tracker that only *sets* state on the
   handful of opcodes it models never clears it. Any unmodelled instruction
   that writes the same register (a load, a `move`, an arithmetic op, a
   multiply, a function return value) leaves the old constant attached, and
   the next store is attributed to a value that was overwritten dozens of
   instructions earlier. Clear the destination register's tracked constant
   on **every** op you do not model, not just on the ones you recognize as
   destructive — but derive the destination from that op's real encoding
   and guard `rd != 0` / `rt != 0`, or encodings that reuse the `rd` field
   for something else (`jal`, `mult`, `div` on MIPS) will clear your
   tracking of the hardwired zero register and poison everything downstream.
2. **Tags lost across sign-extension idioms.** Carrying a derived tag
   ("this register holds the value XOR the mask", "this is field N") only
   through arithmetic misses the shift pairs compilers emit to
   sign/zero-extend: `xori; dsll32; dsra32` on R5900, `sll; sra` on MIPS32,
   `lsl; asr` on ARM, `shl; sar` on x86. Propagate the tag through
   `sll`/`srl`/`sra`/`dsll*`/`dsra*` (value changed, provenance not) or the
   mask vanishes mid-expression and the site is dropped as unknown.
3. **Recording scoped to the loop you expected.** Gating event recording on
   the structure you came to find (`if (col >= 0)`, "inside the table loop")
   discards exactly the interesting hits: the setters that run *outside* the
   loop, in init or in a special case. Record everything, classify
   afterwards.

**Check / fix:** besides the three rules above, give the scanner a null
control before trusting a count — run it on a word-shuffled copy of the same
region, and against a deliberately rotated expectation. Both should collapse
to zero. A tracker with a stale-state bug often scores *better* on shuffled
input than you would expect, which is the tell.

**Canonical example:** Valkyrie Profile 2 (PS2, `valkyrie`),
`tools/valkyrieprofile2/verify-growth-engine-column-map.ts`. The growth-table
column-map scanner produced a wrong column attribution from a constant left
stale by an unmodelled op, lost the XOR-mask provenance across the R5900
`xori; dsll32; dsra32` sign-extension pair, and omitted every setter outside
the expected `col >= 0` loop. All three were silent; only the null control
on shuffled words exposed the first.

Related: `register-linked-opcode-scan-bitmask-reused-across-encodings.md`
(per-*encoding* fixed-bit masks in the same kind of hand-rolled scanner) and
`field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md` (seed the
constant tracker from function entry, not from the load).

**History:** 1 recorded instance (`valkyrie`).
