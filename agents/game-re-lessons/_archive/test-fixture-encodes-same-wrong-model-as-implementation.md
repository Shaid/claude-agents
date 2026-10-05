# A test fixture built from the same mental model as the code under test can't catch that model being wrong

**When it bites:** a decoder's unit test constructs its own input bytes with
a helper function (not sourced from a real captured file) that writes
fields in the order/position the implementation is believed to read them —
and that belief later turns out to be wrong (a field-order swap, an
off-by-one offset, a wrong bit width). The test passed cleanly, possibly for
a long time and across multiple sessions, and gave zero signal that
anything was wrong.

This is a different failure mode from `hand-computed-test-fixture-vs-real-
run.md` (which is about hand-computing an *expected output value* instead
of running the real implementation to get it). Here the fixture's *input
bytes* are the problem: the helper that builds synthetic file bytes for the
test was written by the same person, in the same session, working from the
same (wrong) understanding of the file format as the decoder itself. The
test therefore doesn't independently exercise the decoder against reality —
it exercises the decoder against a byte layout deliberately constructed to
match the decoder's own assumptions, so a systematic misunderstanding is
invisible by construction, no matter how many assertions the test makes.

Confirmed on Three Hopes' G1T "extra dims" header (`g1t.ts`, `chimera`
project, 2026-09-06): `tools/__tests__/g1t.test.ts` had a
`buildG1TExtraDims(width, height, ...)` helper that wrote `height` at
`abs+0x14` and `width` at `abs+0x18` — the exact same (wrong) order the
buggy `parseG1T` implementation read. The test's assertions
(`expect(texture.width).toBe(288); expect(texture.height).toBe(512)`)
passed every time, because both the fixture writer and the implementation
reader agreed on the same incorrect field order — there was never a chance
for them to disagree. The real bug (the two fields' labels were swapped
relative to the actual file format) was found by an unrelated escalation
that derived the real layout empirically from decoded pixel content, with
no reference to the header struct's assumed shape at all. Fixing the bug
required rewriting the fixture helper's byte-writing order to match the
corrected understanding — simply "fixing the implementation" while leaving
the self-consistent fixture unchanged would have made the existing test
fail (a good sign in this specific case, but only because the corrected
values also happened not to be a no-op under the bug — see the next
paragraph).

**Compounding trap: the existing test's own chosen values can additionally
hide the bug even after the fixture is fixed**, if they don't discriminate
the two candidate orderings. The pre-existing test used `width=288,
height=512` — swapping those two labels produces a *different* pair
(288≠512), so once the fixture was corrected the test would in fact fail
under the old (bugged) code and pass under the new one. But had the test
originally chosen a **square** shape (or any shape where the two field
values matched), a label swap would be a complete no-op and the corrected
test still wouldn't discriminate anything. When adding a regression test
for a suspected field-swap bug, always add a case with genuinely
**different** values for the two fields — don't just fix the existing
fixture and assume its existing test data was already asymmetric enough.

**The same trap with expected *behaviour* instead of fixture bytes — branch
direction and flag semantics.** FFV (SNES)'s event-VM tests (`ceres`,
2026-09-14) asserted that `$F0` yes/no and `$E2` battle-result branches
took the paths the port took, with option names (`yesNoChoice`,
`eventBattleResult`) whose meaning was also the port's own. Both
directions were inverted against `EventCmd_f0`/`EventCmd_e2`, and the
`$E2` flag (`$09c4 & 1`) means *party defeated* (source comments: "branch
if not defeated"), not "successful". A synthetic-script test with two
`$FF`-terminated arms cannot see this: whichever arm the port picks, the
test author picked the same one. Fix: derive the expected path from the
handler's own pointer-advance instructions (`lda #$03 ; jsr AddEventPtr`
then a *conditional* `lda #$04`), name the executor option after the raw
flag semantics (`eventBattleDefeated`), and add a real-ROM trace test where
the inline payload is a `CD xx xx FF` call so that the trace step
immediately after the branch must be the callee's entry (`{script: xx,
offset: 0}`) on one setting and `offset + 7` on the other — an
expectation the port's own model cannot supply.

**Fix:** for any test whose fixture bytes are synthesized by a bespoke
builder function (not a real file), audit that builder's field order/
offsets against the *current* (corrected) understanding whenever the format
understanding changes — a builder written before a correction can silently
keep encoding the pre-correction layout even after the decoder itself is
fixed, and vice versa. Where possible, prefer deriving test fixtures from
a real captured file (or an independently-written reference encoder) over a
hand-built byte-layout helper, specifically because a hand-built helper is
one more place the same wrong mental model can hide.

**A third variant: the composition ORDER of stages inside a multi-step
formula, reinforced by a dated "confirmed" citation in the code and the
spec doc.** FFVI (SNES, `ceres` project, 2026-09-16): a task asked for the
exact real source call order joining an AI attack dispatch to the damage
formula. `attack-data.ts`'s `resolveFfviAttackDamageContext()` already
carried an explicit, dated "Current refinement" comment claiming it applied
random variance/defense *before* the split/back-row/critical-multiplier
stage, "matching the source `CalcDmgMod` -> `CalcAttackEffect` order" — and
`data-structure.md` repeated the same claim. Two unit tests combining
`damageVarianceByte`/`defenseContext` with `targetCount: 2` had hand-typed
expected values computed under that same (wrong) order, and passed. Only a
literal re-trace of a freshly-cloned disassembly (`battle/attack.asm`
`CalcAttackEffect` vs. `battle/calc_dmg.asm` `CalcDmgMod`) — checking which
routine touches the shared `$11b0` scratch register first — showed the real
order is the reverse: split/back-row/multiplier apply once, fully, before
the per-target loop ever calls `CalcDmgMod`. The dated citation, the code
comment, and the passing tests were three independent-*looking* signals
that in fact all traced back to one person's one (wrong) reading of the
disassembly, made at one point in time — none of them was a fresh
re-derivation, so none of them could catch the others' shared mistake.

**Sharpened fix, generalizing past byte layouts and branch direction to any
re-derivable fact:** when a task explicitly asks you to (re-)confirm a call
order, an offset, or an algorithm's exact behavior, re-derive it yourself
from the primary source (disassembly, a reference decoder, the real
protocol) even when an existing doc/comment already claims to have done
so — especially when that citation names only routine/function labels with
no concrete address range or line-level instruction trace, and especially
when the claimed fact is checkable against one shared register/variable
read and written by both routines in question (a cheap, decisive check a
prior pass may simply not have performed as rigorously as its confident
prose suggests). A specific, dated citation with matching tests is *stronger
apparent* evidence than plain undated prose, but it is not *independent*
evidence unless you can tell it was produced by re-deriving from the primary
source rather than by the same reasoning pass that wrote the code.

**The inverse case, worth two seconds of triage when a fixture-driven test
goes red:** a synthetic fixture can also encode an input the implementation
*deliberately rejects*, which makes a correct guard look like a parser bug.
On Valkyrie Profile (PSX), a fixture for a container-chain walker placed the
chain at offset 0; the parser rejects a list offset of 0 because that would
alias the container's own header (which is where the pointer to the chain
lives), so the walk returned `null` and the assertion failed. The guard was
right and the fixture was impossible. So when a hand-built fixture fails,
first ask whether the *input* could occur in a real file at all — check it
against a real instance's values — before touching the code under test.
Unlike the main failure above this one is loud and cheap, but the reflex it
needs is the opposite (distrust the fixture, not the code), which is why it
is worth naming.
