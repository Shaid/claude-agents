# A deferred/queued work item must snapshot transient state at enqueue time if the SAME call's own epilogue clears that state before the queue drains

**When it bites:** porting a source routine that both (a) pushes a
deferred/pending action onto a queue for later execution and (b), in the
same function or its immediate epilogue, unconditionally clears some
per-actor/per-object transient scratch state (a "last hit me"/"currently
selected"/"pending target" byte) — especially when the queue is drained by
a *separate* call the caller makes afterward, not inline before the clear
runs.

The natural, structurally-clean port reads the queue entry as just an
identifier (`{slot, kind}`) and has the drain-time executor re-read
whatever transient field originally justified queuing it (e.g. "who last
attacked this actor") to find its target. This looks correct, compiles
clean, and produces a real, non-empty queue — the bug only shows up as a
silent no-op at drain time: the executor finds the transient field already
reset to its default/null, so it has nothing to act on and either skips
the entry entirely or (worse) resolves a wrong target from stale leftover
state, with zero exception and zero log output pointing at the cause.

Confirmed on FFVI (SNES, `ceres`)'s `CheckRetal`/counterattack port: the
source's `ExecCmd` epilogue runs `CheckRetal` (which queues a pending
Retort/Black Belt counter, keyed off the target's "last attacker" byte)
immediately followed by `AfterAction2` (which unconditionally clears that
same byte for every present actor, once per executed command — not
scoped to only the actor whose action just resolved). A first port
modeled this literally as two sequential function calls
(`checkFfviRetaliation(state, false); clearFfviLastAttackers(state);`)
and had the queue entry re-read `actor.lastAttacker` at drain time
(`drainFfviCounterQueue`, called by the host afterward) — by which point
`clearFfviLastAttackers` had already reset it to `null` for every actor,
including the one that had just been queued. The counter would have
silently done nothing: no target, no damage, no log entry, no error.
Caught only by writing an integration test that actually drained the
queue and asserted a real damage number came out — a unit test on
`checkFfviRetaliation` alone (verifying the entry gets queued) would have
passed and hidden the bug completely, since queuing succeeds; only
draining fails.

**Fix:** when a source routine's own epilogue clears transient state
immediately after (not interleaved with) a queuing step, capture the
value the queued entry will need directly into the queue entry itself at
enqueue time, rather than re-reading a shared/global field at drain time.
Generalize the check: for any deferred-work queue ported from disassembly,
ask "does anything between enqueue and drain reset a field this entry
depends on?" — usually yes, if the source models a one-shot/transient
per-tick signal (hit-this-frame flags, last-attacker bytes, pending-target
selectors) rather than a persistent value. Verify with an integration test
that actually drains the queue and checks a concrete resulting effect
(damage dealt, HP changed), not just that the queue received an entry —
a queue-population-only test is structurally blind to this class of bug.
