# A TODO.md/plan.md status claim survives unverified across session boundaries unless you chase its evidence pointer

**When it bites:** starting work on a TODO.md row (or a plan.md session-log
entry) whose description already reads as settled/confirmed, and you're
about to build the next step on top of it without opening the
`data-structure.md` section its Evidence column points to.

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
