# Re-running an automated pipeline producer step can silently discard a separate, un-wired enrichment step's annotations on the same artifact

**When it bites:** you're about to re-run a pipeline producer step (e.g. `build-assets`) for any reason, such as a perf check or a scoped smoke test, and that step rewrites a shared artifact like `manifest.json` that a separate standalone enrichment script later mutates in place. Also: enrichment fields (aliases, signatures) are suddenly missing while the producer reported success.

The setup: an automated, pipeline-registered "producer" step that
(re)writes the artifact from scratch every run, and a separate, deliberately-standalone
"enrichment" step (a CLI script with its own `main()`, not wired into
`game-config.ts`/the pipeline's step list — see
`step-runs-standalone-but-not-pipeline-registered.md` for the *different*
failure of never being called at all) that reads that same artifact and
mutates it in place, adding fields the producer step doesn't know about.
Re-running the producer alone — for any reason, including one that has
nothing to do with what the enrichment step covers, e.g. a concurrency/
performance verification pass, a scoped/limited-corpus smoke test, or
simply re-running to regenerate one thing — silently reverts the artifact
to its pre-enrichment state. Nothing errors; the fields the enrichment
step added are just gone, and the producer step's own success output
(counts, "N items exported") looks completely normal, giving no signal
that anything regressed.

Confirmed on Drakengard 3 (PS3, `flower` project): `character-dedup.ts`
is an intentional, documented standalone post-processing step (not part
of `buildDrakengard3Assets`) that reads the automated pipeline's
`manifest.json`, computes structural identity signatures, and writes
`boneSignature`/`alias`/`duplicateOf`/animation-clip fields back into it
in place. A later session re-ran the automated `build-assets` step alone
(to measure a `execFileSync`→`execFile` concurrency fix's real wall-clock
speedup) — an entirely unrelated goal — and this silently rewrote
`manifest.json` from scratch, discarding every field the previous
session's `character-dedup.ts` run had added (166 aliased entries,
merged-moveset animation clips on 271 meshes). Caught only because a
later step in the *same* session needed that same enrichment data and
found it missing; not caught by any test or the pipeline's own logging.

**The general trap**: "producer step writes the file, enrichment step
mutates it after" is not a safe ordering guarantee unless something
enforces it — a CI check, a checksum/marker the enrichment step could
leave and the producer could warn about disturbing, or (simplest) a
documented operational rule that anyone re-running the producer must
re-run every downstream enrichment step afterward, regardless of whether
the specific change motivating the producer re-run seems related to what
the enrichment step covers. Don't assume "I only touched the texture
export path" means the character/animation enrichment layer is safe —
if the producer rewrites the *whole* shared artifact rather than
patching only the parts it owns, every enrichment layer built on top of
it is at risk from any producer re-run.

**Fix applied here**: re-ran the standalone enrichment step
(`character-dedup.ts`) in full immediately after noticing the gap, which
correctly re-derived the same result from the still-intact underlying
mesh/texture data (nothing about the *source* data was lost, only the
computed annotations) — confirmed by comparing the re-run's summary
counts against the same session's earlier run and finding them consistent
(minor non-determinism in canonical-duplicate tie-breaking is expected and
harmless; the aliased-cluster and merged-cluster *counts* matching is what
matters). A more durable fix worth considering in a future pass: either
have the producer step preserve/merge existing enrichment fields instead
of overwriting the whole record, or have it detect and warn when it's
about to drop fields it doesn't recognize.
