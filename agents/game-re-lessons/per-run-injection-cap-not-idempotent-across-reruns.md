# A per-run "budget" cap on an append/dedup-by-name injection loop must subtract what's already present, or re-running the pipeline grows state without bound

**When it bites:** a batch/injection pipeline stage caps how much it adds
per invocation (a clip count, a record count, any "inject up to N new
items, skip items already present by name/key" loop), and that stage gets
run more than once against the same already-processed output — which is
routine during iterative fix verification (re-running to confirm fix A,
then again to confirm fix B), not a rare edge case.

Confirmed on Drakengard 3 (`flower` project, `docs/drakengard3/ps3/
data-structure.md` §19): a moveset-merge pass injected animation clips
into meshes, deduplicating by clip *name* against what was already present
and capping new additions at `mergeLimit` (25) **per invocation**. Verifying
two separate algorithm fixes in the same session meant running the pass
three times total against the same corpus. Each run correctly skipped
re-adding already-present clip names, but the cap itself only ever counted
*this run's* additions — never subtracting how many clips a mesh already
had. Result: meshes that should have capped at 25 clips reached 50 after
the second run and 75 after the third, silently, with no error — the bug
affected *every* re-run, not just meshes touched by either fix being
verified.

**The general trap**: "dedup by name, cap new additions per run" is not the
same guarantee as "cap the total." A loop that computes
`if (newItemsThisRun.length >= perRunCap) stop` will always add up to
`perRunCap` more on every re-run, regardless of how much is already there,
because nothing in that condition reads the pre-existing count.

**Fix**: compute `remainingBudget = totalBudget - alreadyPresentCount`
once, before the loop, and cap against that instead. Verify idempotency
directly — run the pipeline stage twice in a row against the same input
and assert the second run adds zero new items — rather than trusting "it
skips duplicates by name" as sufficient (that only prevents the same exact
item twice, not the total from growing via *different* items each run).

**Repairing already-corrupted output**: if the bug already ran for real
before being caught, don't hand-patch the inflated records. For an
append-only injection format (each call only ever appends new data,
existing indices/offsets are never touched — a common shape for binary
formats like glTF buffers with accessors/bufferViews), write a general
inverse/truncate function and verify it byte-exact against "inject only
the first K items from scratch" as a dedicated regression test — this
both repairs the real corpus and becomes a reusable safety net if the same
class of bug recurs. Confirmed working this way (`truncateGltfAnimations`
in `tools/shared/psa-gltf-anim.ts`): reconstructs the pre-injection
accessor/bufferView/buffer boundary from the kept items' own referenced
indices, with a dedicated test proving
`truncate(inject 10 clips, keep 5) === inject 5 clips from scratch`
byte-for-byte.
