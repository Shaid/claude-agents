# Reconstructing a MIPS `j`/`jal` absolute target with `&`/`|` in plain JS numbers can produce a negative result that silently fails a `===` comparison against a positive address literal

**When it bites:** writing a from-scratch MIPS (PSX/PS2/PSP/N64) disassembly
census or verify script that computes a `j`/`jal` instruction's absolute
26-bit-shifted jump target as `((pc + 4) & 0xf0000000) | ((word & 0x3ffffff)
<< 2)` (or any equivalent `&`/`|` combination reconstructing the high nibble
from the current PC and the low bits from the instruction word) — for any
PC whose top nibble is `0x8`-`0xf` (i.e. essentially every real PSX/PS2/PSP
kernel- or user-segment address), the `& 0xf0000000` sub-expression alone
already sets the sign bit, and JavaScript's bitwise operators always
produce a **signed 32-bit** result. The final `|`-combined value comes back
as a negative number, so a later `=== 0x800104d4`-style comparison against
a positive hex literal (or any other positive-looking target address) is
false even when the reconstructed target is numerically correct — with no
thrown error, no NaN, nothing but a silent, wrong-looking FAIL.

## Confirmed case

Valkyrie Profile (PSX) round-215 verify script
(`tools/valkyrieprofile/verify-procrange-item-quality-round215.ts`) computed
a `jal` call target this way to confirm an RNG call
(`jal 0x800104d4`) and a re-invocation of an already-known helper
function, both inside a freshly-found consumer of `actor+0x6a7` bit 1.
Both checks initially reported FAIL despite the raw instruction bytes being
exactly right — `((pc + 4) & 0xf0000000)` evaluated to `-2147483648`
(`0x80000000` read as signed), and OR-ing in the low bits kept the result
negative, so it never equaled the positive literal `0x800104d4` under
`===`.

## Fix

Force the final reconstructed value back to unsigned before comparing (or
storing/keying by) it:

```ts
const target =
  (((pc + 4) & 0xf0000000) | ((word & 0x3ffffff) << 2)) >>> 0;   // <-- the fix
```

`>>> 0` at the point the address is *finished being built*, not at each
intermediate sub-expression — mirrors the same "normalize once, at the
boundary" discipline as `int32array-signed-register-as-unsigned-address.md`,
but the trigger here is different: that lesson is about registers stored in
a signed-typed-array crossing into a memory-access boundary; this one is
about a *plain-number* bitwise reconstruction (no typed array involved at
all) whose intermediate `&`/`|` steps go negative well before any
comparison happens. Both need the same `>>> 0` fix, but a reader chasing
only the typed-array angle can still miss this one. Applies equally to `j`
(unconditional jump) targets, and to any other JS bitwise reconstruction of
a full 32-bit address from separately-computed high/low halves — not just
`jal`.
