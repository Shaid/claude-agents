# A TODO.md/plan.md status claim — or a confident corpus-count number in the spec doc itself — survives unverified across session boundaries unless you re-derive it

**When it bites:** starting work on a TODO.md row (or a plan.md session-log
entry) whose description already reads as settled/confirmed, and you're
about to build the next step on top of it without opening the
`data-structure.md` section its Evidence column points to. **Also** bites
when `data-structure.md` itself states a specific whole-corpus count
("N instances counted recursively via a depth-4 walk") as if it were a
settled fact, and the probe script that produced it either wasn't
committed or no longer exists to audit — a session's plan built entirely
around explaining a "gap" against that number (why coverage is only 12 of
297, say) can spend a full pass rationalizing a number that was simply
wrong from the start, with no bug anywhere in the current code to find.
Confirmed on Drakengard (PS2, `flower` project): a prior session's
`docs/drakengard-cavia-archive-format.md` stated "297 instances [of
`mmodel.bin`] counted recursively" with no surviving probe script; a fresh
walker deliberately built to mirror the production `walkCaviaContainer`
exactly (container-name histogram, not a leaf-only scan) found the true
figure was **12** — self-consistent with every other already-shipped
count (LOD/animation container totals all divided evenly by 12, not 297).
The "297" wasn't a bug to explain, it was never correct. Fix for this
variant: before treating an unaudited whole-corpus count as a planning
premise, re-derive it with a walker that matches the real production code
path, not the prose.

Wizardry 6 Amiga's `docs/wizardry6/TODO.md` carried this row forward across
a full session boundary: *"Section 6 is now confirmed (400×32B monster
encounter/spawn groups, independently re-verified against the monster
catalog — e.g. record 5 decodes to a legible 7-species group)."* Confident
prose, a specific example, an "independently re-verified" claim — every
surface signal of a real result. It was never written into
`data-structure.md` or any investigations file at all — a whole-tree `grep`
for the claim's own supporting details (record counts, the "7-species
group" phrasing) found nothing. Dispatching a fresh agent to verify it from
scratch found it flatly **wrong**: section 6 is a general scripted
event/opcode table (message-display triggers, probability-gated recursion,
dice rolls), not monster data — refuted by fresh disassembly plus an exact
statistical cross-check (174/174 and 46/46 field matches against a
different, correct interpretation) that took under an hour to produce.

The failure isn't "an agent hallucinated" (this project's existing
`verify-escalation-artifacts-not-just-claims.md` already covers not trusting
specialist output blindly) — it's narrower and easier to miss: **the
project's own convention says tracker files (`TODO.md`, `plan.md`) point at
evidence, they don't contain it.** A well-written status row is
indistinguishable, by tone alone, from a genuinely verified one. Nothing
about *reading* the row tells you whether anyone ever actually chased its
Evidence pointer and found real disassembly/statistics behind it, versus a
plausible-sounding summary an agent wrote and a later session's own summary
just re-stated without re-checking.

The fix: before treating any TODO.md/plan.md claim as a starting assumption
for further work — not just before treating it as fully closed — open the
doc section its Evidence column names. If that section doesn't actually
contain the specific claim (not just related material), the claim has never
been substantiated regardless of how it reads, and needs to be re-derived
or refuted from scratch, not carried forward. This costs one `grep`/`Read`
and is cheap enough to do for every row you're about to build on, not just
ones that feel suspicious.
