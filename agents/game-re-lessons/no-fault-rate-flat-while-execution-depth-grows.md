# A "% runs without fault" metric stays flat (or regresses) exactly when you replace stubs with real logic

**When it bites:** a corpus-wide sweep runs every script/module/asset
through a bounded interpreter, emulator, or decoder and reports a headline
rate — "% clean", "% no unimplemented opcode", "% parsed without error",
"N/M modules pass". You spend a round promoting stubs to real
implementations, or feeding real data where the harness previously fed
zeros, and the headline does not move. Or it gets worse. The temptation is
to call the round a wash, revert, or go hunting for a regression that is
not there.

## The trap

A no-fault rate measures **where the first fault is, not whether the
interesting code was reached.** A stub is a perfectly quiet way to skip
work: a run idles past code it never executes, returns a plausible zero,
and finishes "clean" having done nothing. Replace the stub with real logic
and the run goes *further* — and then hits the next unmodelled thing. Each
newly-reachable region contributes its own first-faults, so the error count
rises in direct proportion to how much more of the real program you are now
executing.

The metric is not lying; it is answering a different question than the one
you care about. The two can move in opposite directions indefinitely while
the work is going well.

## Check / fix

Never report a first-fault rate alone. Pair it with at least one **depth**
metric, chosen so that only real progress can move it:

- events reaching the target function (damage resolutions, draw calls,
  decoded records) per run;
- count of runs that completed with **no gameplay-relevant stub taken** —
  i.e. the stub table instrumented, not just present;
- instructions/opcodes executed, or distinct basic blocks covered;
- distinct call targets resolved to real code rather than a hook.

Then **classify every new fault before judging the round**: a *content gap*
(the run reached real code that needs data or a hook you have not written
yet — expected, and evidence of progress) versus a *logic bug* (the run
reached code you believe you modelled and it disagreed — the only kind that
should block). A round whose errors tripled entirely from content gaps,
while a depth metric went up an order of magnitude, is a good round.

Corollary for the regression gate: assert on the depth metric and on the
*logic-bug* count. Gating CI on the raw no-fault rate punishes exactly the
commits that add real behaviour, and rewards re-stubbing.

**Canonical example:** Valkyrie Profile (PSX), round 229 of the gameplay-
logic campaign. The interpreter sweep's clean rate was unchanged (48.5% →
48.5%) and erroring module/arena pairs rose 2 → 15 — while damage events
actually reaching `resolveHit` went 4 → 71-81 per run, and the number of
enemy behaviour modules that ran with no gameplay-relevant stub taken went
2 → 540. Every one of the 13 new errors was a content gap in
newly-reachable code. Judged on the headline alone the round looked like a
regression; judged on depth it was the largest single jump in the sweep's
history. (`docs/valkyrieprofile/psx/battle-logic.md` § 115.7.)

**Variants:**
- Same shape with the denominator instead of the numerator: a decoder that
  starts parsing a previously-skipped record type makes its own per-record
  error rate worse while total records decoded rises. Report absolute
  decoded counts next to the rate.
- The inverse direction is its own lesson: a *clean* batch rate that is
  clean only because placeholder content cannot fail — see
  `all-zero-stub-file-inflates-failure-count.md` (benign failures inflating
  a failure count) and `statistical-proxy-blind-to-whole-body-visual-defect.md`
  (an aggregate metric passing over a real defect).

**History:** 1 confirmed instance (valkyrie, round 229).
