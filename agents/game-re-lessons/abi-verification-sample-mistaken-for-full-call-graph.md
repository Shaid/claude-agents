# A small ABI cross-check sample of a shared function's call sites is not its call graph

**When it bites:** a shared/utility function's calling convention or ABI was
confirmed against a handful of call sites (an "N sites checked, all agree on
this signature" sample, often cited as "N call sites" in a doc section), and
a later open item's scoping decision ("every caller of this function needs
X, which is out of scope") rests on that same small N — especially when the
open item's own framing repeats the sample's count as if it were the
function's total caller population.

## What went wrong

Valkyrie Profile (PSX, `valkyrie`): the shared battle damage-formula/hit-test
caller `resolveHit` (`fcn.8005b9e0`) had its calling convention confirmed
against 6 call sites (5 ordinary compiled overlay code + 1 per-creature
behaviour-module example) — a deliberately small, representative sample
picked to nail down the ABI once, cited in the docs as "§ 37.1's five call
sites." A later open item ("a single-target swing's impact point is
always-passing because it's authored by the attacker's behaviour-module
bytecode, out of scope") implicitly generalized that 6-site sample to *every*
caller of `resolveHit` — treating "6 sites checked, 5 overlay + 1 module"
as if it meant "the function has roughly this many callers, mostly module
code." An exhaustive whole-binary caller census (a `jal 0x8005b9e0` byte-
pattern scan, not a re-read of the ABI section) found the real call graph was
**471 sites**: 5 overlay-resident (a fixed, small set — the ABI sample had
already found all of them) and 466 module-resident. The scoping question
"is the impact point always module-authored" was never actually tested
against the real population — it was answered from a sample that happened to
contain 5/6 module examples purely because the ABI-confirmation pass wanted
variety, not because modules dominate the call graph in that ratio.

Escalating with the corrected framing ("re-derive the real caller count
before trusting the scoping verdict") found the 5 overlay-resident sites are
ordinary compiled arithmetic on already-modeled fields (caster/target
position, facing, formation depth) — fully implementable with zero contact
with the excluded module-interpreter scope — while only the 466 module-
resident sites (the real majority, but a materially different fraction than
"5 of 6 checked") were genuinely out of scope. The open item was correct in
direction but wrong in magnitude, and that wrongness hid real, cheaply
gettable progress.

## The generalizable fix

- When an ABI/calling-convention confirmation cites "N call sites checked,"
  treat N as a *sample size for the ABI question*, never as an estimate of
  the function's total caller population, unless the doc explicitly says the
  sample is exhaustive.
- Before accepting or writing a scoping verdict that says "every caller of
  shared function F needs subsystem X, so this is out of scope," run (or
  re-run) an exhaustive whole-binary caller census for F's own address —
  the same census technique `sibling-functions-outside-callgraph-scope.md`
  and `unbounded-caller-census-crosses-sibling-routine-boundary.md` already
  use for other purposes. Partition the real population into "reachable via
  ordinary compiled code" vs. "reachable only via the excluded subsystem"
  before generalizing either way.
- A small fraction of the population (here, 5/471 ≈ 1%) can still be fully
  in-scope and fully implementable even when the excluded subsystem
  genuinely dominates the count — don't let "the excluded subsystem is the
  majority" collapse into "the excluded subsystem is the whole answer."
  Ship what the minority allows before writing the residual off as blocked.
