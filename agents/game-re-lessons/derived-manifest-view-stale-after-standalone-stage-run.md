# A pipeline stage run standalone writes correct assets that the viewer never sees, when the step deriving the consumer's view lives only in the full-pipeline function

**When it bites:** you ran one stage directly
(`npx tsx tools/<game>/build-<thing>.ts`) rather than the whole pipeline,
it logged success and wrote correct output plus a correct `manifest.json` —
and the consumer (viewer/site) still shows the previous run's assets, with
no error anywhere. Also bites when reviewing any pipeline whose
`buildAssets()` ends with a finalize/derive/index step that no stage calls
on its own.

Seer pipelines commonly write a flat `manifest.json` per stage and then, in
`buildAssets()` *after every stage has run*, derive the artifacts the
consumer actually reads — sharded `manifest/<category>.json` files, a
`categories.json` index, a search index. A stage invoked on its own updates
the flat manifest correctly and never touches the derived view, so the
derived view keeps describing assets that may no longer exist. Nothing
validates the two against each other at read time, so the failure is
completely silent.

## What happened

FE Warriors: Three Hopes (`chimera`). `build-animations.ts` was rewritten to
emit 27 sharded GLBs in place of a single `common.glb`, and its standalone
run reported exactly that: 27 files written, stale `common.glb`/`common.json`
deleted, `manifest.json` updated with 27 correct `animation` entries. But
`writeShardedManifest()` was called only from `build-assets.ts`, so
`manifest/animation.json` still held **one** entry, naming the `common.glb`
that had just been deleted. Everything the stage was responsible for was
right; the consumer's view was a run behind and pointed at a missing file.

## The fix

Extract the finalize step into a shared helper and call it from **both** the
full pipeline and each stage's own CLI entrypoint:

```ts
// manifest-categories.ts — shared, so no caller can forget it
export function finalizeShardedManifest(outDir: string): void {
  const full = JSON.parse(readFileSync(resolve(outDir, 'manifest.json'), 'utf8'));
  const index = writeShardedManifest(outDir, full, CATEGORY_DISPLAY_NAMES);
  verifyShardedManifestOnDisk(outDir, full.length);   // throws on any mismatch
}

// build-<stage>.ts — standalone entrypoint only; buildAssets() calls it itself
if (isStandalone) {
  buildStage().then(() => finalizeShardedManifest(outDir));
}
```

Guard it to the standalone branch so a full pipeline pass doesn't re-derive
per stage (and doesn't derive from a half-populated manifest mid-run).

## How to catch it in review

Grep for the derive/index call (`writeShardedManifest`, "build search
index", "write categories") and check how many call sites it has. **One call
site, inside the all-stages function, is the bug.** Then confirm from the
consumer's side, not the producer's: after a standalone stage run, the
derived file's entry count must match the flat manifest's count for that
category — a `verifyShardedManifestOnDisk`-style assertion inside the helper
makes that automatic on every future run.

Distinct from the neighbours: `step-runs-standalone-but-not-pipeline-
registered.md` is the mirror image (the stage works alone but the *pipeline*
never invokes it); `always-full-run-manifest-merge-accumulates-stale-
entries.md` is about the flat manifest's own merge semantics going wrong.
Here the producer and the flat manifest are both correct, and only the
derived view the consumer reads is stale.
