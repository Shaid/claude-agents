# "Not called near each other" doesn't refute "same subsystem" — find the shared caller before concluding disjoint

**When it bites:** two resources/functions are being classified as either
"part of the same subsystem" or "unrelated" based on whether their own
loader/consumer call sites sit near each other or reference one another
directly — especially when that verdict is backed only by asset-shape
inference (small pixel dimensions "must be" an icon, not scenery; a
palette-variant "must be" cosmetic) rather than by having traced upward to
find whether the two functions share a common caller.

Confirmed on Dune (Amiga, `wyrm` project). A first pass concluded
`ornycab.hsq` (a full-screen cockpit picture) and `dunes`/`dunes2`/
`dunes3.hsq` (small, ≤210×86px sprite atlases) belonged to unrelated
subsystems: it found `ornycab`'s one call site, found the `dunes*` cluster's
call sites, observed neither called the other or referenced a shared local
table, and — reinforced by the small decoded sprite dimensions looking
icon-shaped rather than scenery-shaped — wrote up "loaded nowhere near
ornycab's code... an unrelated world-map/travel-path subsystem." That
verdict rested entirely on the *local* call sites of each function; it never
traced upward from either one to ask "what calls the function that calls
this."

A second pass (prompted by an external correction — the actual player of
the game knew both were part of the same ornithopter-travel view) traced
callers one level further and found `LAB_02B0`, a shared subroutine
installed from a dozen-plus sites across the game, whose body calls the
`dunes*`-loading cluster and then, a few instructions later, the function
that gates `ornycab`'s display. The two "unrelated" resources were steps
of the *same function*. The first pass's search was locally exhaustive
(every call site of each target was found) but never widened one level up
the call tree — the same blind spot as
`sibling-functions-outside-callgraph-scope.md`, but applied to a
classification verdict ("these are unrelated subsystems") rather than to
"where does this input come from."

The asset-shape reasoning compounded the error rather than independently
confirming it: small sprite dimensions were treated as sufficient evidence
of functional role ("small = icon atlas, not a scenery layer") without ever
reading the code that actually draws those sprites. That code (a per-object
position-plus-inverse-scale computation reading a travel-distance state,
redrawn every tick, each object's stored distance decremented on every
redraw) turned out to be a genuine scaling parallax blit — individually
small source sprites scaled up/down at draw time are exactly what a
CPU-side pseudo-3D scenery renderer looks like, and shape alone couldn't
distinguish that from a fixed-size icon.

**The fix, generalized:**
1. Before writing up "these two resources/functions are unrelated" from
   local call-site evidence, trace at least one level upward from each —
   find their immediate callers, and check whether those callers share a
   common parent (directly, or via an installed-callback slot both are
   steps of). A negative built only from each node's own call sites proves
   "not directly calling each other," never "not part of one caller's
   sequence."
2. Don't let a resource's decoded pixel/dimension shape substitute for
   reading its actual runtime consumer. "Looks icon-sized" is a weak prior
   at best; the consumer code (does it recompute this sprite's position
   and size every frame from some other state, or just blit it once at a
   fixed spot?) is the real test.
3. When a corrected working hypothesis (a played-game description, a
   sibling port's known behavior) contradicts a prior static-trace verdict
   built on scope this narrow, re-verifying by widening the caller search
   is usually cheap and often decisive — don't just re-read the same call
   sites again expecting a different read.
