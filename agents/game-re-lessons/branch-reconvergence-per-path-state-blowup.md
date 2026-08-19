# A per-path DFS with cloned state explodes combinatorially at reconverging branches, even though each individual walk terminates fast

**When it bites:** extending an already-verified, both-branches-following
control-flow walker (originally built just to collect data-independent
records like faces/instructions) to ALSO thread mutable interpreter state
(a matrix stack, register file, accumulator) forward through the walk, and
choosing real recursion with a visited-set cloned per branch so that two
paths carrying genuinely different state don't corrupt each other.

## What went wrong

Frontier: Elite II's model bytecode has a global-visited, both-branches
worklist walker (`walk_bytecode`) already verified byte-exact against a
community oracle for collecting geometry instructions — correct, because
face/line records don't depend on any interpreter *state*, only on which
byte offsets are reachable. Extending this to resolve submodel-reference
transforms required also tracking a small 3x3 matrix stack that DOES vary
along a path (mutated by dedicated opcodes). The natural-looking fix was
real recursion at every branch, with the visited-set threaded *per path*
(not shared) so that two branches reaching the same instruction with
different matrix state wouldn't silently collide.

This blew up: one model's bytecode, which the original global-visited
walker resolves as exactly 7 real submodel-reference instructions,
produced 2,112 "submodel call" events under the per-path walker — each
individual `run()` call terminated in milliseconds, but a whole-corpus
assembly pass that should take ~1s took >120s and had to be killed. The
mechanism is classic diamond reconvergence: a run of N sequential
IF/IF_NOT branches, each spawning a recursive call for the jump target
while the surrounding loop continues down the fallthrough, replays the
*shared tail* once per branch combination — a small, fixed instruction
count exploding into an exponential number of walks.

## The fix

Go back to a single **global**-visited worklist (matching the original,
already-verified structure exactly), threading the interpreter state
through worklist entries `(pc, state...)` rather than through per-call
recursion. This collapses dedup back to "first path to reach an
instruction wins," at the cost of possibly using the wrong (not
path-specific) state for an instruction reachable via two branches with
genuinely divergent preceding mutations. Before accepting that tradeoff,
quantify how often it can actually matter: here, the state-mutating opcode
had only 4 hits in the entire corpus, so the tradeoff was clearly the right
call, and this was confirmed by re-verifying the walker's *other* outputs
(submodel-call field decode) against the oracle byte-offset-aligned
afterward with 0 regressions.

General principle: **whenever a state-threading extension is added to an
existing branch-following walker, re-derive whether the extension is safe
under the ORIGINAL dedup discipline before switching dedup strategies.**
If the state genuinely needs true per-path fidelity, memoize on
`(offset, state-hash)` instead of `(offset,)` alone — cheaper than
unmemoized real recursion, and doesn't reopen the diamond-blowup risk.
