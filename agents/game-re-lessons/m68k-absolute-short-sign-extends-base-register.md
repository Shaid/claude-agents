# 68000 absolute-short (`.w`) addressing sign-extends before masking to the 24-bit bus

**When it bites:** disassembly shows a state/scratch-RAM base register
loaded via `lea.l $NNNN.w, An` (or `movea.l #$NNNN, An` with a 16-bit-
looking immediate) where `$NNNN`'s top bit is set (`$8000`-`$FFFF`), and
you're about to treat that register's value as literally `$0000NNNN` when
computing every `(d16,An)`-relative field address that follows.

## What went wrong / the underlying fact

The 68000's absolute-short (`.w`) addressing mode does not zero-extend its
16-bit operand to form the 32-bit effective address — it **sign-extends**
it, then the CPU masks the result to its 24-bit address bus (bits 24-31
ignored). `lea.l $8000.w, a5` therefore does not set `a5 = $00008000`; it
sets `a5 = $FFFF8000`, which masks to `$FF8000` — squarely inside 68000
work RAM (`$FF0000-$FFFFFF` on this class of hardware), not low memory.
Confirmed on Knights of the Round (CPS1, `kolbold` project): a
(re)initialization routine's `lea.l $8000.w, a5` is the literal instruction
that pins the "state RAM" base register every `NNNN(a5)`-relative field
throughout the game's disassembly is offset from — a prior session's docs
used that addressing convention extensively without ever citing the
instruction that establishes the base's actual value, leaving it an
unstated assumption until this session traced it directly.

This is the same underlying CPU fact as `moveq-sign-extend-lsl-w-wraps-
negative-index.md` (an 8-bit immediate sign-extending before a `.w`-sized
shift/index computation) but a different instruction class entirely
(absolute-short *addressing mode* on a `lea`/`movea`, not an immediate-load
instruction feeding an indexed effective address) — worth checking both
when a 68000 disassembly's numbers don't add up.

## The fix

Before treating any `.w`-suffixed absolute or immediate 68000 operand as a
plain zero-extended value, check its top bit. If set, the real 32-bit (then
24-bit-masked) value has `$FFxx` or `$FFFFxx` in its upper bytes, not
zeros — for a `.w`-addressed base register specifically, values in the
upper half of the 16-bit range (`$8000-$FFFF`) resolve into the *top* of
the 24-bit address space (typically work RAM on this era of hardware),
while values in the lower half (`$0000-$7FFF`) resolve to literal low
addresses (typically ROM/ISR-vector space) — decide which region a given
`.w` operand lands in from this rule, not from where you expect the base
"should" be.
