# A whole-file bias tracker's caller-saved-register invalidation rule is a sound over-approximation that produces real false negatives

**When it bites:** a whole-file/whole-function linear bias-tracking census
(the kind that resolves `$s0`/`$a1`-relative struct-field accesses back to a
known base like "the actor record") treats ANY earlier `jal`/`call`/`jr`
instruction in its linear scan as invalidating a register's tracked bias,
on the reasoning that the register is caller-saved and the call could have
clobbered it — and reports a clean "no producer/consumer found" negative
for a field that a real, compiled function DOES access through exactly
that register.

## The trap

The invalidation rule is not wrong as an ISA-level fact: a caller-saved
register's value is genuinely undefined after a call unless the callee is
known not to touch it. But a compiler routinely leaves a function's own
INCOMING PARAMETER live in a caller-saved register across an unrelated call
to a different helper, for the simple reason that the callee doesn't
clobber it and reloading would waste an instruction. Small, leaf-like
handler functions — a property-setter, a dispatch-table callee, anything
compiled as "receive a pointer argument, do a little work, maybe call one
unrelated utility, then use the pointer again" — hit this constantly. A
whole-file census applying the invalidation rule literally, with no
per-function callee analysis, treats every such handler's own later use of
its own parameter as unresolvable, even though the parameter was never
actually reloaded.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`), round 18 of the `vp1psx-scene-script-
opcodes` campaign: the project's whole-overlay bias tracker (used to
resolve struct-field accesses off `$s0`/`$a1`/etc. back to the 264-byte
actor record) treats `$a1` — the incoming actor-pointer argument every
`SETPROP` property-handler function receives — as invalidated by any
earlier `jal`/`jr` anywhere in its linear scan, since `$a1` is caller-saved
under the MIPS o32 ABI. Four real `SETPROP` handlers (property ids
44/47/24/48, closing four separate open flag bits) address the actor record
directly through `$a1` after an earlier unrelated call elsewhere in the
same function body, and none of them ever reload it — a completely
ordinary compiler output. The bias-tracking census reported zero hits for
all four, even though each producer was a two-instruction, byte-exact-
confirmable `lw`/`andi`-or-`ori`/`sw` sequence sitting in plain sight. A
separate, bias-FREE literal scan (`lw $r,0xe4($any)`/`0xe8($any)` — no bias
requirement, no ABI reasoning at all, 366 hits overlay-wide) plus the same
forward bit-chase found all four immediately.

## The fix

Treat the caller-saved-invalidation rule as what it is: a sound
OVER-approximation (it never produces a false positive — a bias it keeps
live really is live) but a real, structural source of false NEGATIVES on
common, unremarkable code shapes. The correct response is not to try to
make the bias tracker itself smarter about which specific calls really
clobber a register (that needs whole-callee analysis the project's static
tooling doesn't do, and would need re-deriving per callee) — it's to always
pair a bias-tracking census with a bias-free literal-operand fallback scan
(match the literal displacement/immediate directly off ANY base register,
with no bias/liveness reasoning attached) before concluding a field has no
producer or consumer. Run the fallback as standard practice on every "zero
hits" bias-tracker result before writing up a negative, not just after
noticing a suspicious gap — the whole-file linear scan's own conservative
ABI assumption is common enough to expect on any project resolving
struct-field access on a real compiled-code corpus, not a one-off VP1
quirk. Not MIPS-specific: the same shape recurs on any calling convention
with caller-saved registers (x86 `%eax`/`%ecx`/`%edx`, ARM `r0`-`r3`, 68k's
`d0`-`d1`/`a0`-`a1`) whenever a whole-binary census applies a blanket
ABI-liveness rule with no per-callee side-effect knowledge.
