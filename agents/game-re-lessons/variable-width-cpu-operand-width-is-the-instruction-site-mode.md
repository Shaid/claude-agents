# On a variable-width CPU, a value's width is the M/X mode at the instruction that reads, compares, or decrements it — not the width it was stored or masked with

**When it bites:** porting 65816 (SNES) — or any CPU with a runtime
accumulator/index-width flag — where a value is stored through an 8-bit
mask (`and #$00ff`), loaded from a byte-sized-looking address, or compared
after a byte store, and the port picks the operand width from *where the
value came from* instead of from the `REP`/`SEP` state in force at the
instruction actually consuming it. The symptom is a decode that is right
for every small value and silently wrong for the rest (a high byte
dropped, a wraparound at the wrong modulus, a sign test that can never
fire).

## Three instances from one FFV (SNES) event-VM audit (`ceres`, 2026-09-14)

1. **Decrement width.** `$CE/$CF` repeat counts are stored `lda $df ; and
   #$00ff ; sta $1166,x` — an 8-bit value — but `NextEventCmd` decrements
   the counter under `longa` (`lda $1162,x ; dec ; sta $1162,x`, 16-bit).
   An encoded zero therefore wraps to `$FFFF` and runs 65,536 passes. A
   prior "small fix" had asserted 256 passes from the store-side mask, and
   its doc/test carried the wrong modulus forward.
2. **Load width.** `$D1/$D7` timer event IDs are read `longa ; lda $e0 ;
   sta $0afe` — 16-bit, spanning operand bytes b2/b3. The port read one
   byte; 51/60 and 4/4 ROM uses had a nonzero high byte (`d1 00 01 05` =
   event `$0501`, not `$001`). Cheap census that catches it: every decoded
   ID must index the real pointer table (`< count`) *and* a high-byte-
   nonzero count across the corpus tells you whether the wide read
   matters.
3. **Compare width.** `DrawHiryuu` computes a 16-bit signed sprite X,
   stores its low byte, then tests that byte with `cmp #$f8` to set the
   OAM X-high bit — only X in `-8..-1` (low byte `$F8..$FF`) qualifies.
   The port compared the unmasked signed value (`x >= 0xf8`), which is
   never true (positive X is capped below `$F8` by the clip test and
   negative X is < 0), so the bit could never be set.

## Fix

Before porting any arithmetic/comparison on a variable-width CPU, locate
the nearest upstream `REP`/`SEP` (or `longa`/`shorta` macro) on the path
to *that* instruction and take the width from it; then mask the ported
intermediate to that width at the same point the CPU would (`& 0xffff`
for a 16-bit `dec`, `& 0xff` before an 8-bit `cmp`). The width at the
store and the width at the consumer are independent facts. This is the
semantic twin of `r2-snes-flag-width-blind.md` (which is about
*disassembling* the bytes correctly) — here the disassembly was right and
the port still chose the wrong width.
