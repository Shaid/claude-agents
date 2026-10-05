# A `cp N`/`jr c`/`jp m`-style two-branch clamp idiom is not a symmetric range clamp — it tests sign, not unsigned range

**When it bites:** disassembling a small "clamp this byte to [0, N]" code
sequence built from a compare plus two conditional branches (Z80 `cp N` /
`jr c,<pass-through>` / `ld a,N` / `jp m,<done>` / `xor a`, or the
68k/6502-equivalent `cmp`+`bcs`+`bmi` shape) and describing its behavior as
a plain `clamp(value, 0, N)` without simulating all 256 input bytes first.

## What happened

Tracing ddsom's (CPS2) per-tick vibrato/pitch-bend computation
(`audiocpu+0x1f66`-`0x1f76`) found exactly this shape clamping an 8-bit sum
to a 0-0x6b table index:

```
cp 0x6c
jr c, <pass-through: a unchanged>
ld a, 0x6b
jp m, <done: keep 0x6b>
xor a              ; else: a := 0
```

Simulating the real Z80 flag semantics for every input byte 0-255 (not
just spot-checking a couple of values) showed the clamp is **asymmetric**:
inputs in `[0x00, 0x6b]` pass through unchanged (as expected), but inputs
in `[0x6c, 0xeb]` clamp to **0**, while only inputs in `[0xec, 0xff]` clamp
to the expected ceiling (`0x6b`). A plain `clamp(value, 0, 0x6b)` would
have gotten the `[0x6c, 0xeb]` case wrong. The cause: `jp m` after the `cp`
tests the **sign flag** of the byte result `(value - 0x6c) mod 256`, not a
literal "is value negative" or "is value out of range" test — for a
positive `value` in `[0x6c, 0xeb]`, `value - 0x6c` is `[0x00, 0x7f]`
(sign bit clear), which routes to the "else" branch (0), not the ceiling
branch. Only when `value - 0x6c` itself overflows into the negative half
(`[0x80, 0xff]`, i.e. `value >= 0xec`) does the sign-flag branch fire.

## The fix

Never describe a 2-branch compare-based clamp as a symmetric range clamp
from the mnemonics alone. Simulate (by hand or in a short script) every
possible input byte through the *exact* flag semantics of the real
opcodes (Z80's `cp`/`jr c`(carry, unsigned borrow)/`jp m`(sign flag of the
subtraction result) — or the target CPU's equivalent), and document the
real per-range boundaries you get, even if they look "wrong" or seem to
disagree with an assumed clean clamp. A cheap 2-instruction clamp idiom
producing an asymmetric result is a real, common consequence of using a
sign-flag test as a shortcut for a range test, not a bug in the analysis
— documenting a real asymmetry (rather than smoothing it into a "clean"
clamp description) is what let a downstream cross-check (an independently
found `0x6bff` accumulator-clamp constant from an unrelated call site)
land on the exact same real boundary value, confirming both traces.
