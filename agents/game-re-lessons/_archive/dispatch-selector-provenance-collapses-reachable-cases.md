# An N-case dispatcher's selector may itself be forced to a near-constant value — trace its provenance before sampling case bodies

**When it bites:** you've confirmed a jump-table/dispatcher exists (its
existence, its case count, and that it does get called), and the natural next
step looks like "sample/trace some subset of the N cases, prioritizing the
mechanically-significant-looking ones." Before doing that, trace where the
selector value itself comes from — it may not range freely over the case
space at all.

## What went wrong (worked example)

Valkyrie Profile (PSX, `valkyrie`): the post-death "special behaviour"
dispatcher (`fcn.80034838`) has a 32-entry jump table, keyed on a 5-bit
selector masked from `actor+0x128`. The open item read "confirmed to exist,
~32 cases, only trigger traced" and the natural plan was to sample as many
of the 32 case bodies as the round's budget allowed.

Instead, the selector's *own* provenance was traced one level up:
`actor+0x128` is unconditionally overwritten with `actor+0x5b7`'s value
whenever the death state (`actor+0x129`) is 2. That looked like it just moved
the question one field over — until `actor+0x5b7`'s own writer was traced
too, landing in a **different overlay entirely** (TOC slot 1491, not the
battle overlay the dispatcher itself lives in): a shared actor-init routine
(`fcn.8009ae4c`) unconditionally zeroes `actor+0x5b7` for every enemy record,
with no code path that ever writes anything else to it for that record kind.

The selector is therefore **hardcoded to 0 for every enemy, always** — not a
per-record, per-move, or RNG-derived value ranging over 0-31. A corpus census
of all 1992 enemy move-entry records across both discs confirmed this isn't
just "usually 0": the field the dispatcher actually reads (move slot 0's own
`field0a & 0x1f`, since the forced index bypasses per-move variation) takes
only 6 distinct values corpus-wide. 26 of the 32 jump-table entries — including
one that byte-aliases a *different* function's own internal table via linker
adjacency — are provably unreachable, not merely unsampled. "Trace 32 cases"
collapsed to "trace 6 cases, and prove the other 26 dead" — a fundamentally
cheaper and more complete task than the one the open item's own framing
implied.

## The generalizable fix

Before spending budget sampling an N-case dispatcher's bodies:

1. Find the selector's own defining instruction(s), not just the `andi`/mask
   that narrows it to the table's index width.
2. If the selector is itself copied/forced from another field (not computed
   fresh from record data each call), trace **that** field's writers too —
   don't stop at the first level of indirection. The real writer can sit in a
   sibling overlay/module the dispatcher's own file doesn't contain.
3. Once the selector's true value space is known, run a corpus-wide census of
   the *actual* input field (not an assumption about it) to get an exact
   count of which case indices are reachable and how often. A jump table's
   declared size is not evidence of its reachable size.
4. Only then prioritize tracing among the cases the census says are real —
   this usually shrinks "trace up to N cases" to "trace the K cases that can
   actually fire," turning a bounded-effort partial-progress task into a
   completable one.

This is a specific, more actionable version of the general principle in
`negative-from-addressing-root-not-shapes.md` and complements
`index-writer-may-be-a-loop-counter-not-a-selection.md` (which asks "is this
even a selection at all?") — this lesson assumes it *is* a real selection and
asks "how much of the declared case space can this selection actually reach?"
before treating case-sampling coverage as the metric of progress.

## Follow-up (same project, same function, a later round): the collapse itself was scoped to one caller, not the dispatcher

`fcn.80034838`'s "selector forced to 0, 6 of 32 cases reachable" verdict
above was correct — for the one death-dispatch call site (`state==2`) that
motivated finding the function in the first place. A later round ran an
exhaustive whole-binary `jal 0x80034838` census (something the original
"trace the selector's provenance" pass never did, because the function
had already been named "the enemy death dispatcher" from its one known
caller, which discouraged asking whether it had others) and found **7
real call sites**, not 1. The other 6 never set `actor+0x129=2` and take a
second branch — sitting in the function's own prologue, `0x8003486c`-
`0x80034900`, entirely BEFORE the address (`0x800348f4`) the original
verify script's first assertion checked — with a completely different
selector source (a small helper function's return value, itself reusing
an already-confirmed table via a different addressing path) and an extra
target-refresh step the death path never runs. The 26-of-32-cases-dead
conclusion is still correct for the death path specifically; it was never
true of the dispatcher as a whole, because the dispatcher as a whole was
never censused.

**Added fix, before declaring any dispatcher's reachable-case collapse
final:**

5. Run an exhaustive whole-binary caller census for the dispatcher
   function's own address (a plain `jal`/`bl`/`call`-target scan, not a
   re-read of the one call site that led you here). A function found and
   named from a single motivating caller is not evidence it has only one
   real caller.
6. Disassemble the dispatcher's own body starting from its true prologue
   (the first stack-frame-adjust instruction), not from wherever your
   trace of the motivating call site happened to start checking
   instructions. If your existing verify script's first cited address is
   not the function's own entry point, the untouched gap before it is
   unread territory — and, as here, it can hold an entire second
   selector-provenance branch gated on the very state flag that made the
   first call site special in the first place.

## Second follow-up: the collapse can be one layer further up, in the selector's *own* upstream lookup table

The 6 non-death call sites `fcn.80034838`'s §100 follow-up found feed
`actor+0x128` from a *different* selector source than the death path's
`actor+0x5b7` forcing — a small helper (`fcn.800301fc`) that reads a
3-slot per-actor table (`actor+0x5b4..+0x5b6`) as a rotate/lookup. The
natural next step looked like "census this new selector source the same
way §99.4 censused the old one" — a real corpus scan of what the *helper*
outputs. But the helper's own fast path is `table[j]` for a small index
`j`, and the table itself turned out to be a **hardcoded engine constant**
for the enemy side: the function that builds it (`fcn.8009eb44`) sets
`table[i] = i` (i=0..2) unconditionally, not from any per-enemy data. That
degenerate table makes the whole helper the identity function of `j` for
every enemy — so the "new" selector source is really just the same
already-decoded driving counter (`actionsUsed`) read straight through, and
the already-verified census technique (§99.4's `field0a & 0x1f` scan)
needed only its loop bound widened (slot 0 only → slot
`0..actionsPerPhase-1`) to answer the question. Reachable set came back
byte-identical to the death path's own.

**Generalizes:** when a dispatcher's selector is fed through an
intermediate lookup/rotate table rather than a raw counter, check whether
*that table itself* is degenerate (a hardcoded ramp, an all-same-value
fill, a table the engine builds identically regardless of input) before
assuming its output ranges over the table's declared width. A lookup
table with `N` slots is not evidence its content varies across those `N`
slots — the same "declared size is not evidence of reachable size"
principle from the base lesson applies one level up the data-flow chain,
not just at the dispatcher's own case count. And once a table is confirmed
degenerate, an already-verified census script over the *real* driving
value usually needs only a changed loop bound, not a new decoder.
