# An unnamed argument, a shared gating flag, or a bounded-either-way outcome can settle a "race" outright — check before building machinery to order two mechanisms

**When it bites:** a stalled open question is framed as *which of two
writers / handlers / display objects wins*, or *which of two orderings
applies* — "these two both stamp the field; establishing the order needs
the per-frame driver's scheduling", "a real timing question between two
independently-triggered objects that static analysis cannot settle", "we'd
have to emulate to see which runs first", "no live/emulator confirmation
that X visually tracks Y" — and one of three things is true: (a) somewhere
in the dispatch that reaches them sits an argument, flag or struct field
still carried in the docs as unnamed (`extra`, `unk`, `flags`, `arg3`); (b)
one of the two mechanisms has its *own* reachability gated on a variable
(often a shared global flag) that the *other* mechanism sets; or (c) both
orderings really are runtime-dependent and genuinely unpinnable from static
bytes alone, but the mechanism's own arithmetic makes the *visible outcome*
identical, or bounded to an imperceptible/non-diverging difference, either
way. Decode that argument, trace that gate, or work the bound through,
first. It may not order the two paths at all; it may mean only one of them
is ever reachable, that they aren't actually independent, or that the free
variable a live capture would have observed doesn't matter — and the "race"
dissolves into a plain reachability fact or an invariance proof, either of
which is stronger evidence than a live capture would have given anyway. The
tell that this is happening: the question's own framing names a mechanism
**nobody has traced yet** (a frame scheduler, a tick order, a driver's call
sequence) as the thing that must be built before the question can be
answered, or asserts the two objects are "independently-triggered" without
having checked one's entry gate against the other's known side effects, or
declares "needs live capture" for an outcome question when the full
mechanism on both sides is *already* fully decoded and only the ordering
itself is unpinned. That is usually the shape of a wrong premise, not of a
hard problem.

## Shape 1: an untraced call argument selects the path

Valkyrie Profile (PSX). `docs/valkyrieprofile/psx/battle-logic.md` § 63.8
carried, as a still-open row:

> Which slot-7 duration actually survives for `Dampen Magic`. Two writers
> race: the spell's own `turn + 3` at `0x8005ce6c` (at status-*request* time)
> and `fcn.80046938`'s generic slot-7 `turn + 2` at `0x80046aa4` (at
> status-*apply* time, one driver tick later) … establishing the order needs
> the apply driver's scheduling relative to the popup handler's own frame.

The shared request routine had been traced two sections earlier as
`fcn.80077340(target=a0, statusMask=a1, extra=a2)` — the third argument named
`extra` and never revisited. It is an **immediate-apply flag**. Its epilogue:

```
800774e8  beq  $s4, $zero, ...   ; nothing accepted -> return 0
800774ec  sll  $v0, $s6, 16      ; DELAY SLOT: the flag ($s6 = a2)
800774f0  beq  $v0, $zero, ...   ; flag clear -> just return 1
800774f8  lhu  $v0, 0x59e($s1)
80077500  or   $v0, $v0, $s7     ; |= the REQUESTED mask
80077504  sh   $v0, 0x59e($s1)   ; the status is active immediately
```

The spell passes `1`, so the status is already active when the request
returns; the generic apply driver `fcn.80046938` therefore **never runs on
that path at all**, and the writer the row named (`0x80046aa4`) is not the
writer. A third function's already-active branch does it (`0x80046c90`). There
was never anything to schedule. 3 of the 16 corpus call sites pass `1`; the
other 13 pass `0`.

### Two corollaries worth reusing

**Duplicated presentation code next to a flag is a tell for a path-selecting
flag.** All three sites that pass `1` hand-roll the popup and SFX the generic
driver would otherwise have produced — a duplicate copy of a status-name
string, an SFX id issued inline. That duplication looks like redundancy until
you realise it exists *because* the flag suppresses the generic path. If two
call sites of one routine differ only in an unnamed argument and one of them
also carries a near-copy of a downstream handler's side effects, the argument
is almost certainly selecting between them.

**Null-control a path claim by patching one operand, not by checking the
value.** Under a concrete-execution harness, the control was replacing the
call site's own `addiu $a2,$zero,1` with `addu $a2,$zero,$zero`, and
separately `nop`-ing the flag's store at `0x80077504` — each flipping *which
instruction made the final store* while the stored **value was identical on
both paths** (`turn + 2` either way). A value-only comparison could not have
distinguished "the flag decides the path" from "the value coincides"; only
recording the storing PC did. When two candidate paths converge on the same
number, instrument the writer's identity, not the number.

## Shape 2: one mechanism's own gate reads a flag the other sets

Valkyrie Profile (PSX) again, a later item. The Feathered Pocketwatch item's
"undo" was left open across two full passes with this exact framing
(`item-skill-system.md` §§ 9.10.5, 9.12.4): the item spawns a 20-frame
fade-out object whose per-object `0x63` state hard-writes `actor+0x04 = 5`
to every actor 30 frames after dispatch; a *separate* per-seat menu-open/
close routine can spawn a fade-**in** that writes `actor+0x04 = 4` back. Both
passes called "does the fade-in land before or after the 30-frame write" "a
real timing question between two independently-triggered display objects
that static analysis cannot settle" — and neither checked whether the
fade-in's own entry point was gated on anything.

It was. Both of the fade-in's call sites sit behind one gate:

```
800a1d84  lui  $a0, 0x8008
800a1d88  lw   $a0, -0x3bf4($a0)      ; a0 = ctx
800a1d90  lhu  $v0, 0x111e($a0)       ; the FULL ctx->0x111e halfword
800a1d98  bne  $v0, $zero, 0x800a1e8c ; skip the whole fade-in block unless ==0
```

`ctx->0x111e` is exactly the freeze-bit field the Pocketwatch's own
dispatcher sets and — per an already-completed, unrelated exhaustive census
of its own state machine — never clears. So the fade-in cannot fire *at all*
while the freeze bit is set, which is the Pocketwatch's entire active
lifetime; the 30-frame hard-write always lands first, and the "race" was
never a race — the two objects share a gate, so they are not independent.

## Shape 3: the ordering is genuinely free, but the outcome isn't

Valkyrie Profile (PSX) again. `FUN_80039b5c`, the field engine's per-frame
position-integration commit, sweeps a 96-slot actor array in slot order; a
"slaved" (rider) actor reads its anchor's already-committed position if the
anchor sits at a *lower* slot, or its not-yet-committed (stale) position if
the anchor sits at a *higher* slot — and no static table pins slot
assignment, since it's a runtime spawn-order fact. Two prior passes closed
every OTHER sub-item of this exact mechanism (the attach math, the
eligibility test, the flag bits) and left exactly one item open: "no live/
emulator confirmation that a rider visually tracks a moving platform in-
game — static evidence only, explicitly out of scope." Nobody had asked
whether the ordering, though genuinely unpinnable, actually changes what
gets displayed.

It doesn't, to more than one frame's worth of velocity. Deriving both cases
from the already-decoded formula (`rider.x = anchor.x + xOffset`, `rider.y
= anchor.y + anchor.velY + anchor.gravityVelY + yOffset`): if the anchor
commits first, `anchor.x`/`anchor.y` already include this frame's delta, so
X comes out exact while Y *overshoots* by exactly this frame's `(velY +
gravityVelY)` (the formula's own compensating term double-counts a delta
that already landed). If the anchor commits after, `anchor.x`/`anchor.y`
are still last frame's values, so Y comes out exact while X *lags* by
exactly this frame's `velX`. Either ordering: one axis tracks exactly, the
other is off by precisely that frame's own velocity term — never a running
sum, because each frame re-reads the anchor's real current fields, so no
error is ever folded into stored state. This was verified computationally,
not just by hand algebra: running the project's own already-ported,
byte-exact formula for both orderings against a **time-varying** (not
constant) anchor velocity for 500 frames confirmed the per-frame equality
and the absence of drift between the run's first and last quarter — a
sinusoidal, not constant, driving signal is what makes a passing per-frame
check attributable to the formula's structure rather than a coincidence at
one fixed value.

The discipline generalizes from shapes 1/2: before accepting "the ordering
is genuinely runtime-dependent, so this needs live capture," check whether
the mechanism's own arithmetic makes the two orderings' outputs
**equivalent or boundedly close** — run the ALREADY-PORTED, already-
verified formula (or its raw disassembled equivalent) for both orderings
against a suitably varying input and diff the results, rather than
concluding a live capture is the only way to observe which ordering "really"
happens. A live capture would only ever have shown you one ordering anyway
— proving the outcome is invariant (or bounded) across *both* is strictly
stronger evidence, and it's free once the mechanism is fully decoded on
both ends.

All three shapes share one discipline: an unnamed dispatch **argument**
puts only one writer on the path (shape 1); an unchecked entry **gate**
makes one mechanism unreachable while the other's precondition holds (shape
2, close kin of `guarded-call-confirmed-called-but-precondition-unreachable.md`,
but about ordering two mechanisms rather than refuting one call); or the
mechanism's own arithmetic bounds the outcome regardless of which case
occurs (shape 3). Before accepting "static analysis cannot settle this —
it's a genuine runtime race," disassemble BOTH mechanisms' own entry
conditions and check for a shared variable between them, and — if the
ordering really is free — work through whether the formula itself makes
the outcome invariant, not just each one's already-documented effects.

## Related

`gating-argument-may-be-a-compile-time-constant-not-data.md` is the adjacent
case — trace a gating argument's *origin* and it may be a hardcoded literal,
making live-looking code dead. Same discipline (an untraced argument or gate
invalidates a settled-looking verdict), opposite direction.
