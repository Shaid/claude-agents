# A verify script that thoroughly checks a callee's own internals proves nothing about who calls it

**When it bites:** a doc's chain-shaped narrative ("function A calls B,
which — on some condition — calls C") is backed by a verify script with
many passing checks, and you're about to trust the whole chain because the
script looks exhaustive. Check specifically whether any of those checks
pins a literal `jal`/`bl`/`call`/`JSR` instruction *from* the claimed
caller *to* the next link — a script can be genuinely thorough about one
function's arguments, gate conditions, and formula constants while never
once verifying the calling relationship the surrounding prose asserts.

## The trap

Verifying a callee's internals and verifying a specific caller's edge to
that callee are two independent claims, even though a single paragraph of
prose usually states them together as one continuous story. A script with
33+ passing checks reads as "this whole chain is confirmed," but each
check only proves what it actually tests — volume of PASS output for one
sub-claim creates no evidence at all for a neighboring, unchecked sub-claim
in the same sentence.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`): a round's `battle-logic.md` section
named a 4-link AOE/splash-damage chain — spawner installs a per-tick
handler, the handler "calls the sweep function, then (on a positive sweep
result) calls the damage applicator" — and shipped a verify script with
33+ checks per disc. Every check was real and passed: the applicator's
30%-multiplier magic-multiply, its `battleCtx` nullify-flag gates, its HP
clamp, its PWS/combo-gauge hooks, the handler's own discriminator/mutex
tests, the spawner's zero-caller/one-construction-site census. None of
them pinned a literal `jal` from the handler to the applicator. A later
round's fresh whole-overlay `jal`-target census found the applicator has
exactly one static caller anywhere in the overlay — and it sits *inside
the sweep function itself*, not the per-tick handler. The handler's own 4
`jal` targets are the sweep, a shared GTE projector, and two unrelated
visual/animation-invocation helpers; it calls the sweep only for a
geometric side effect and discards the sweep's return value without ever
branching on it. The sweep's real return value was also misdescribed as
"a target actor pointer" when it's actually a 0/1 "did anything get hit"
flag — a second sub-claim the same script's thoroughness on the
applicator's internals gave no coverage of at all.

## Fix

When writing or reviewing a verify script for a chain-shaped claim,
enumerate the individual edges the prose asserts (A calls B; B's return
value gates whether C is called; etc.) as a checklist *separate* from each
link's own internal-behavior checks, and confirm every edge has its own
literal-instruction pin (a `jal`/`call` census, not an assumption from
argument shape or narrative position — see
`trampoline-role-guessed-not-resolved.md` for the sibling trap on
*indirect* calls specifically). A script that is exhaustive about
internals but silent on edges will pass cleanly forever without ever
having tested the thing the surrounding prose actually claims.
