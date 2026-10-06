# 68000 `moveq #imm,Dn` sign-extends before `lsl.w` scales it — a "large" index can wrap to a small negative displacement

**When it bites:** hand-computing a PC-relative indexed-addressing target
(`TABLE(pc,Dn.w)`) fed by a `moveq #imm,Dn` immediately followed by
`lsl.w #N,Dn` (a common 68000 idiom for "load a small constant, then scale
it into a table-entry byte offset") — especially when the immediate is in
the upper half of `moveq`'s range (`0x80`-`0xff`) and a naive unsigned
`imm * (1<<N)` computation of the resulting table offset lands on
plausible-looking-but-wrong data (still in-bounds, structurally
consistent bytes, just not the row you expected), or on obvious garbage
you're tempted to blame on a wrong table base instead.

## What went wrong / the underlying fact

`MOVEQ #imm,Dn` sign-extends its 8-bit immediate to the full 32-bit
register — `moveq #$ff,d0` sets `d0 = 0xFFFFFFFF` (-1), not `0x000000FF`
(255). A following `LSL.W #N,Dn` then operates on only the **low 16 bits**
of that register, with the result also confined to 16 bits (no carry into
the upper word) — so `d0.w = 0xFFFF`, shifted left by 2, wraps mod 65536
to `0xFFFC` (still as a 16-bit value). When that register then feeds a
`(d16,PC,Dn.w)`-style effective-address computation, the CPU sign-extends
the **word-sized** index register value to 32 bits for the addition:
`0xFFFC` as a signed 16-bit word is `-4`. The real effective address is
therefore `TABLE_BASE + (-4)`, i.e. **4 bytes before** the labeled table
address — not `TABLE_BASE + (0xff * 4)` (an unsigned "index 255"
interpretation, which for a compact table is usually far out of bounds or
lands in unrelated code/data) and not `TABLE_BASE + 0` either.

Confirmed on D&D: Tower of Doom (ddtod, CPS2): a boot/reset-adjacent code
block calls into a palette-bank-load function's *midpoint* (bypassing its
own `moveq #$0,d0; move.b (a5,d),d0` prologue) with `moveq #$fc,d0`
immediately before it, then the function does `lsl.w #$2,d0; movea.l
TABLE(pc,d0.w),a2`. `0xfc` sign-extends to `0xFFFFFFFC`; `lsl.w #2` on the
low word gives `0xFFF0` = `-16` signed; the real read is `TABLE - 16`, four
entries *before* the labeled table start — and that address held a real,
well-formed ROM pointer (verified: consecutive 4-byte entries each exactly
0x400 apart, matching a real palette-page-table stride), while the naively
unsigned-computed offset (`TABLE + 0xfc*4`) landed on unrelated garbage
bytes entirely.

## The fix / the generalizable lesson

Never compute a `moveq`-then-`lsl`-then-indexed-addressing offset with
plain unsigned arithmetic. Trace the actual register width and sign
semantics at each step: (1) `moveq` sign-extends its 8-bit immediate to
32 bits; (2) a `.w`-suffixed shift/logical op that follows operates on
(and leaves its result confined to) the low 16 bits only; (3) a
PC/An-relative indexed-addressing mode with a `.w`-sized index register
sign-extends that 16-bit value before adding it to the base. A call site
that bypasses a function's normal parameter-setup prologue (jumping
straight into the middle, past a `moveq #$0,d0` or similar) and instead
pre-loads the index register with its own constant is a strong signal the
author is deliberately exploiting this wraparound to reach a *negative*
offset from the labeled table anchor — check entries *before* the table
label, not just increasingly-large ones after it, when a "boundary" index
value (`0xff`, `0xfe`, `0xfc`, ...) doesn't resolve to anything sensible
under unsigned arithmetic.

---

## Instance 2026-10-06 (inbox candidate, verbatim; the d8(An,Dn.w) note is the part merged here)

# A bounded 68k call harness settles tilemap/metatile ordering where alignment search plateaus at ~50%

When it bites: reconstructed stage maps align only about half the cells.
Lesson: run the game's own init/stream routine in a flat-memory Musashi harness and diff VRAM cells. A 50% plateau meant wrong premises, not wrong offsets: maps stored bottom-up (flip per metatile, not per tile), one attr byte per metatile, two record sizes (17/33 B with collision bytes), row counts from map-to-table gaps. Also 68k `d8(An,Dn.w)` sign-extends the index, which splits reads past 0x8000.
