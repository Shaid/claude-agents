# A handful of manually-probed samples can miss a dominant sub-format entirely — run the real batch pipeline before writing "this varies" into docs

**When it bites:** hunting for a suspected-common feature/chunk/magic
inside a container/resource type by manually reading a small number of
samples (an 8-10-item probe script, not the real extractor), finding it in
few or none of them, and being tempted to write that up as "this
sub-format varies" or "this is rare, not universal" — especially before
the real batch/pipeline extractor has ever been run over the *whole*
corpus of that type.

## What happened

Confirmed on The 3rd Birthday (PSP, `~/Development/parasite`): while
reverse-engineering the `SEDBSSCF` audio-database container (244 entries
in the real corpus), a quick manual Python probe read 8-9 samples (fsd
table indices 33-40, a contiguous run near the start of the entry list)
looking for an embedded `RIFF`/`WAVE` chunk. It found **zero** — only one
separately-sampled entry elsewhere in the table (index 66) had a findable
chunk. This was written into the in-progress doc as "the sub-format
clearly varies... not universal."

Running the *real* extractor (`build-assets.ts`'s `buildSedbsscfAudioAssets()`)
over the complete 244-entry corpus in the same session found a findable
`RIFF`/`WAVE` chunk in **229/244 (93.9%)** of them — the overwhelmingly
dominant shape, not a rare exception. The 8 manually-sampled misses were
real (that specific contiguous run of entries genuinely lacks a findable
chunk within the scan window), but they were not remotely representative
of the format as a whole — likely because contiguous table entries
correlate with some other grouping (build order, source folder, a shared
sub-type) that this session never identified.

## The fix

- Treat a small manual probe (single digits to low tens of samples) as
  informative for *presence* ("does this feature exist at all in this
  container type") but **not** for *prevalence* ("is it common or rare").
  Prevalence claims need either a real statistical sample (random, not the
  first/nearest N table entries) or — cheaper and better when available —
  the real batch pipeline run over the full corpus, which was already
  being built anyway.
- If a prevalence claim must go into docs before the full pipeline has
  run, hedge it explicitly ("N/M sampled, not yet run at scale") rather
  than asserting a qualitative characterization ("varies", "rare",
  "the common case") that reads as settled.
- When the real full-corpus number *does* come in and contradicts an
  earlier small-sample characterization, supersede the doc section in
  place with a `> **Correction:**` block (per this project's own doc
  convention) rather than just quietly fixing the number — the wrong
  small-sample generalization is itself worth recording so a future pass
  doesn't repeat the same probe-then-conclude shortcut.

## Generalization

This is the corpus-scale cousin of `format-field-width-unexercised-by-
first-corpus.md` (which is about one field's *value range* being
underexercised by a small/early sample) and is distinct from
`sparse-sample-flatness-heuristic-false-negative-on-real-content.md`
(which is about a *shipped pipeline's own* sparse-pixel-sampling
heuristic missing real content *within* one asset). This lesson is about
an *investigator's own* small, often non-random manual draw *across* a
corpus, made before the real batch tooling exists to just check
everything — the fix is procedural (build/run the real extractor before
generalizing), not statistical (there's no heuristic to tune here). Any
"I checked N samples and found X in only a few of them" finding is
worth treating as provisional until the real pipeline — which is usually
being built in the same session anyway — confirms it at full scale.
