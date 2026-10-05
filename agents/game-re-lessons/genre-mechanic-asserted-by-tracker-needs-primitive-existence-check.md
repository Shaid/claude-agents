# A tracker row can assert a named genre mechanic the game does not have — check the engine owns the required primitive before hunting for its table

**When it bites:** a `TODO.md` row, a plan, or a task brief states as
*settled background* that the game implements some named mechanic of its
genre — "random encounter pool", "step counter", "encounter rate",
"day/night cycle", "morale system", "aggro radius" — and the work assigned
is to find that mechanic's data table. The framing is inherited rather than
re-derived, so the hunt starts from "where is the pool" instead of "is
there a pool." Bites hardest when the mechanic is so standard for the genre
that nobody thinks to question it.

Confirmed on Valkyrie Profile (PSX). The row `vp1psx-random-encounter-pools`
read, as established context: *"They are reached through the 1,147
stack-form launchers whose argument is computed at run time — VP1's random
encounters, which draw a bundle from a pool."* The task brief repeated it
verbatim. Every clause was false. VP1's dungeons are side-scrolling
platformer rooms with **visible** monsters you walk into: there are no
random encounters, no pool, no encounter rate, and the "computed at run
time" argument turned out to be parameter 0 of a shared linked-library
helper whose callers all push compile-time literals (see
`runtime-valued-script-operand-is-usually-a-parameter.md`). The real answer
was not a table that resisted decoding — it was a mechanism that does not
exist.

**The disproof was available in minutes and should have been step 1.** The
scene VM's 238-entry opcode dispatch table was *already fully enumerated in
this project's own source*, and it contains no random-number opcode at all.
A script therefore physically cannot randomise its own argument, so no
amount of searching could ever have found a per-room probability table. An
already-enumerated opcode table, syscall table, VM instruction set, or
library import list is a **free existence proof or disproof** for any
mechanic that would need a primitive from it — RNG for randomness, a timer
or step hook for rate, a clock read for time-of-day.

**Fix:** when a row hands you a named genre mechanic, spend the first few
minutes asking what primitive the engine would *have* to expose for that
mechanic to be implementable at all, then check whether it exposes it —
preferably in an enumeration the project already owns, so the check costs a
grep. If the primitive is absent, the mechanic is refuted and the real
question becomes "what does the game do instead," which is usually a much
easier and more interesting trace. Report the refutation explicitly and fix
the row's wording; an unchallenged framing propagates to the next session's
brief exactly as this one did.

This is the existence-check sibling of `tracker-prose-is-not-evidence.md`
(which says re-derive a row's *claims*) and of
`domain-refuted-by-shape-not-values.md` (which says shape/range matches are
weak evidence for a domain). The addition here: the strongest and cheapest
check on a *mechanism* claim is not re-deriving its evidence, it is asking
whether the engine has the capability the claim presupposes.
