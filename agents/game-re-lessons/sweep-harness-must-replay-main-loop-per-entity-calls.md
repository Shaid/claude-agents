# A sweep that only calls the script handler N times never advances the state the main loop owns

**When it bites:** you are running a corpus of game-script / behaviour
modules under an interpreter or emulator harness, driving each one by
calling its handler (think `update()`, the AI tick, the state-machine entry
point) some number of times. The modules run clean, but the behaviour you
actually wanted to observe — a damage resolution, a projectile spawn, a hit
frame, a sound trigger, a state transition — never happens, at any iteration
count. The natural conclusion is "missing content/data" or "this module
needs a real scene", and it is usually wrong.

## The trap

In a real engine the per-entity handler is only one of several things the
frame does. Frame counters, animation gates, cooldown timers, duration
fields and deferred-callback lists are typically advanced by **other calls
the main loop makes**, not by the handler — a per-actor decrement pass, an
apply-animation-frame call, a pooled-object/particle tick, a collision
sweep, a message-queue drain. The script merely *tests* the gate the loop
maintains.

So a harness that calls the handler in a bare loop reproduces one of the
frame's N phases. Every gate the other phases own stays pinned at its
initial value forever, and the handler spins on a condition that can never
become true. This looks identical to missing data, and it is immune to
raising the iteration count — which is the diagnostic tell: *if more
iterations never help at all, the loop is missing a phase, not a value.*

## Check / fix

Before concluding "content gap", **disassemble the main loop** and
enumerate what it calls per entity and per pool each frame, not just the
dispatch to the script. Then replicate those phases in the sweep's own tick,
in the real order. Specifically look for:

- a counter the handler reads but nothing in the handler writes — someone
  else decrements it (grep for every writer of that offset, not just
  readers);
- `for each actor: f(actor)` / `for each pooled object: obj->vtbl->tick()`
  shaped loops adjacent to the script dispatch;
- an apply/commit phase that rewrites the same fields the handler set
  (animation frame, transform, flags) after the scripts have all run;
- callback invocation that happens from a *pool* tick rather than from the
  owning actor, so the entity's own handler is not on the call path at all.

Only after the tick mirrors those phases does a persistent "never reaches
X" count as a real content gap.

**Canonical example:** Valkyrie Profile (PSX). Enemy behaviour modules ran
under the project's MIPS interpreter but no module ever reached `resolveHit`,
however many handler calls were made. Three separate main-loop-owned
mechanisms were missing: `animationStep` only advances a frame when actor
`+0x63 == 0`, and `+0x63` is set by `startAnimation`, **decremented by a
per-actor tick pass**, and rewritten by `applyAnimationFrame` — none of
which the handler itself does; and `resolveHit` is not called by the actor
at all, but from the **pooled display-object tick handlers**. Adding those
phases to the sweep tick took damage events from 4 to 71-81 per run and
gameplay-stub-free modules from 2 to 540.
(`docs/valkyrieprofile/psx/battle-logic.md` §§ 113.3, 115.2-115.3.)

**Variants:**
- Same failure with a frame/VBlank hook: the harness never raises the
  interrupt, so an engine that does all its state advance in the vblank
  handler is entirely inert while every script "runs".
- Phase *order* matters as much as presence: running the apply/commit pass
  before the scripts rather than after makes the scripts observe last
  frame's state and can produce plausible-but-wrong behaviour instead of no
  behaviour, which is harder to spot.

Related: `game-re-method/bounded-interpreter-with-hook-table.md` and
`game-re-method/cpu-emulation-boot-harness.md` cover building the
interpreter itself; this lesson is about the fidelity of the *driver* loop
on top of it. `no-fault-rate-flat-while-execution-depth-grows.md` is the
metric trap you will hit immediately after fixing this.

**History:** 1 confirmed instance (valkyrie, rounds 113/229).
