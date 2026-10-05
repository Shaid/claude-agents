# A traced consumer's non-branching use of a value can sit well past the first branch that tests it

**When it bites:** manually reading forward from a call site to characterize
what a caller does with a returned/computed value, and stopping once the
first conditional branch tests some bits of it — especially when the
untested remaining bits (a status code's high nibble, a flags word's unused
byte) look "obviously discarded" simply because no branch differentiates on
them.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 26 of the
`vp1psx-scene-script-opcodes` campaign. `FUN_80034018` returns a packed
status word: bit 0 means "matched via the tight/settled-only margin," and
bits 8-15 (a nibble `0x9`/`0xa`/`0xb`/`0xc`) identify which of 4 geometric
corner cases matched. Two call sites, right after the `jal`, run a plain
`andi $v0,$a0,0x1` / `beq` on bit 0. Reading only that far made it look like
the high nibble was purely diagnostic — computed inside the callee, tested
by nobody, effectively dead weight on the return value.

Continuing to read forward past that branch — about a dozen more
instructions, with no further branch in between — found `and
$v0,$a0,$v0; sll $v1,$s3,16; or $s5,$v0,$v1`: the untouched high byte of the
status word gets masked out, OR'd together with the candidate actor's own
outer-loop index, and stored into the shared accumulator register `$s5`,
which becomes the enclosing loop's real per-actor "anchor candidate" result.
The nibble was consumed the entire time — just not via a branch, so a trace
that stopped at the first one missed it completely.

## Fix

When manually tracing a value's consumption, don't stop reading at the
first conditional branch that tests part of it. Keep reading forward
(bounded by the function's real end, or until the register holding the
value is genuinely redefined for something unrelated) for a later,
non-branching use of whatever bits the branch didn't test — a store, a
field write, or an `and`/`or`-into-accumulator pack are all just as real a
"consumer" as a branch, and none of them leave a control-flow signal to
notice from a distance. A branch is the most *visible* form of consumption,
not the only one; treating "no branch differentiates on these bits" as
equivalent to "these bits are discarded" is the trap. This is a manual-
reading-discipline sibling of `dataflow-chase-must-track-destination-not-
mere-reference.md` (which covers the analogous correctness rule for an
*automated* register-chain tracer) — same underlying principle, different
failure surface: a human stopping too early versus a tool's continuation
rule being wrong.
