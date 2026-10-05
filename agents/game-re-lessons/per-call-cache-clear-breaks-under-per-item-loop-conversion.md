# Converting a "runs once per refresh" function into a per-item loop can expose a shared-cache-clobbering bug that was previously invisible

**When it bites:** fixing a "toggle only applies to the primary item, not
every tracked item" bug (see
`secondary-attach-api-misses-primary-side-effect-wiring.md`) by wrapping an
existing per-model/per-object refresh function in a loop over all tracked
items. Before shipping that loop, check whether the function's OWN body
clears or invalidates a cache/global it does not own exclusively — a
function that was only ever called once per refresh cycle can safely
"clear everything, then rebuild what I need" internally; the same function
called N times in a row (once per tracked item) will have call 2 wipe out
call 1's freshly-rebuilt state for a DIFFERENT item, and call 3 wipe out
call 2's, and so on — silently leaving only the LAST item in the loop with
correct state.

Confirmed on `@seer-project/engine-3d`'s `applyMeshShading(model, cache,
opts)`: its first action was `clearGeneratedShadingMaterials(cache)` —
disposing and evicting every entry in the whole shared shading-material
cache, not just entries belonging to `model`. This was correct and
harmless when the function ran exactly once per appearance refresh (a
single primary model). When fixing the sibling bug above by looping this
same function once per `trackedModels[]` entry, the loop's second iteration
would have called `clearGeneratedShadingMaterials(cache)` again — wiping
out the shading materials the FIRST iteration had just finished building
for a different model — and so on for each subsequent model, leaving only
the last-processed model with real materials and every earlier one either
broken or falling back to defaults. This was caught by reasoning through
the loop's effect before shipping, not by a failing test (no test existed
yet that called the function twice in a row against a shared cache).

**The fix:** scope the cache-clearing to only the current call's own
model — traverse that model's own meshes and evict/dispose only THEIR
cache entries (by mesh or by whatever key the cache uses), instead of
calling a blanket "clear everything" helper. Verified against the existing
single-call regression test (still passes — a lone call still disposes its
own stale materials) plus new tests that call the function twice in
sequence against one shared cache and assert both models' materials
survive.

**Generalizable premise-trap:** converting "a function that runs once per
refresh, cycle, or frame" into "a function called once per item in a loop"
is a distinct bug class from ordinary loop-conversion bugs (off-by-one,
wrong iteration variable). The risk isn't in the loop itself — it's in
whatever the function's body does to STATE IT DOESN'T EXCLUSIVELY OWN
(a shared cache, a global counter, a module-level Map/Set) under the
assumption "this only runs once, so a blanket clear/reset is fine." Before
looping any existing function that used to run once, read its body
specifically for `clear`/`reset`/`dispose`-shaped calls against anything
wider in scope than the single argument it was passed, and scope those
down to the current item's own key/subset first.
