# A shared `manifest.json` upserted by concurrent sibling agents in the same session can lose an already-written batch to a timing race, even with correct upsert-by-name logic

**When it bites:** more than one agent (or process) is running pipeline
stages against the *same* project's `manifest.json` in the same session
(a common shape when several extraction stages — mesh, texture, audio,
animation — are parceled out to sibling agents running concurrently), your
own stage does the standard "read the whole file once at start, accumulate
new entries in memory, periodically write the whole thing back" pattern,
and after a run the manifest's per-type entry count comes up short of what
your own run's console log actually reported writing — especially by an
amount matching an *earlier*, now-superseded run of your own stage (a smoke
test, a `--limit=N` dry run) rather than anything from this run.

## What happened

Chimera (FE Warriors: Three Hopes, Switch), extending `build-audio.ts` to
extract a second audio resource type. A small `--limit=5` smoke test wrote
334 real tracks + manifest entries first (to validate the new decode path
before committing to a slow full pass), then a separate full extraction run
started later and wrote 13,345 more. Both runs individually logged success
with correct counts. But the *final* `manifest.json` only had 13,345 audio
entries from this stage, not 13,679 — a gap of exactly 334, matching the
earlier smoke test's own output count precisely. The 334 `.wav` **files**
were still on disk, untouched; only their manifest *entries* were gone.

The mechanism: this project's `manifest.json` is a single shared file that
several sibling agents' pipeline stages (mesh/texture/animation, owned by
other agents in the same session) all upsert-by-name against, each doing
its own independent read-accumulate-write cycle with no locking and no
re-read mid-run. Sometime between the smoke test finishing (334 entries
now on disk) and the full run starting (which read the file fresh at its
own start), a concurrent sibling stage must have read an *older* snapshot
that predated the 334-entry write, then written its own updated snapshot
back afterward — silently overwriting the smoke test's addition with a
version that never had it. The full run's own initial read then inherited
that already-diminished baseline and correctly built on top of it, so
nothing about the full run's own logic was wrong; the loss happened
entirely in the gap between two other read-write cycles it never
participated in.

This is a **different failure mode** from the already-documented manifest
pitfalls:
- `always-full-run-manifest-merge-accumulates-stale-entries.md` is about
  one source drifting against its own *past* output (temporal staleness),
  or a same-process type-filtered merge dropping a sibling *type's*
  entries on every run.
- `content-addressed-manifest-merge-needs-source-precedence.md` is about
  two sources whose *content* legitimately collides under the same key and
  needs an explicit precedence rule.
- This one is a plain **lost-update race** (a TOCTOU/read-modify-write
  race) between two otherwise-correct concurrent writers of the *same*
  logical source (two runs of the same stage, or two different stages —
  either can be the "victim" or the "clobberer"), with no content
  collision and no staleness in either writer's own logic — just bad
  timing between processes that never coordinate.

## The tell

Cross-check the manifest's per-category/per-group entry count against an
independent, disk-level ground truth your own stage controls — the actual
output *file* count on disk (`ls <outputDir>/*.wav | wc -l`), not just the
manifest. A shortfall that (a) doesn't match any decode-error count your
own run logged, and (b) matches a *specific* earlier run's own reported
output count almost exactly, is the race's signature — it means an entire
batch got silently dropped between two writes, not that anything failed to
decode.

## The fix

Don't try to add file locking or coordinate with sibling agents (usually
impractical mid-session) — instead, make the loss cheaply *recoverable*
without redoing real work:

1. Keep (or add) a **per-stage incremental progress file** — a small JSON
   list of "already processed" keys (source file paths, RDB ids, whatever
   this stage's own unit of work is), separate from `manifest.json` itself
   and written only by this stage. This project's `build-audio.ts` already
   had this pattern (`.audioAsrsProgress.json`) for resumability across
   crashes — it turned out to double as the race's fix mechanism for free.
2. When the count-mismatch tell above fires, identify which processed keys
   correspond to the missing entries (diff the expected total against what
   survived, or — as done here — recognize the gap matches an earlier run's
   reported count exactly and identify that run's specific keys), remove
   just those keys from the progress file, and re-run the stage. It will
   reprocess only those items — cheap if the real work (decode) is fast —
   regenerating both the output files (harmlessly overwritten with
   byte-identical content) and the manifest entries the race erased.
3. Verify by re-running the count cross-check from the tell above: manifest
   entry count for this stage's category/group should now equal the actual
   file count on disk exactly.

The general principle: any pipeline stage sharing a single accumulated
JSON artifact with concurrently-running sibling agents should treat "read
once, write many times over a long run" as inherently racy, and keep an
independent, cheap way to detect *and regenerate* a lost batch — rather
than trusting that "the merge logic is upsert-by-name, so it's safe."
Upsert-by-name only protects against overwriting *other* entries' *names*;
it does nothing about one writer's whole snapshot clobbering another
writer's more-recent addition when both hold a full in-memory copy across a
long-running process.
