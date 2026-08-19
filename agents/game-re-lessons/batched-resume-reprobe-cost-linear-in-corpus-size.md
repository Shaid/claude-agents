# Re-probing already-decoded items on every resumed batch run costs time linear in total corpus size, not the new batch

**When it bites:** designing (or reviewing) a resumable, batched extraction
pipeline for a large corpus (thousands to tens of thousands of items,
processed via repeated bounded invocations like `run-*-batched.sh`), and
the resume-from-disk path does more than a bare existence check on an
already-decoded item — e.g. re-opening the output file to re-derive its
metadata (a fresh `ffprobe`/header-parse subprocess spawn) so the
manifest's field shape stays "current."

## What went wrong

Confirmed on NieR Replicant ver.1.22474487139 (PC)'s audio pipeline
(`data/sound/*.pck` → MP3, ~28,600 real clips across a projected ~10
batches). After fixing a real manifest field-shape bug (a semantic-category
field that needed correcting), the resume path was changed to re-probe
every already-decoded clip's output file (one `ffprobe` subprocess call
each) and re-push a fresh manifest entry, reasoning that this would keep
resumed entries' metadata current across any future schema change — mirroring
the texture pipeline's own resume-from-disk convention, which *does*
cheaply re-derive metadata on resume (but from an already-in-memory parsed
header, not a fresh subprocess spawn per item).

This is a real, measured performance bug: the cost of resuming N
already-decoded items is **O(N)** subprocess spawns, and N is the *total
corpus size already finished*, not the current batch's own size — so batch
2 of a 10-batch run pays to re-verify batch 1's ~3,000 items before doing
any new work, batch 5 pays to re-verify ~12,000, and batch 10 pays to
re-verify ~27,000, an ever-growing tax that approaches (and can exceed) the
cost of the batch's own new decode work. Reverting to a bare `existsSync`
check with no re-probe (trusting that the run which originally decoded an
item already pushed its correct manifest entry, preserved across runs by
the pipeline's own upsert-by-name manifest merge) measurably improved real
throughput — confirmed directly on this corpus, roughly doubling clips/sec
between the reprobe and no-reprobe versions of the same code, all else
equal (same host, same concurrency, same remaining corpus).

## The fix

- **Default a batched/resumable pipeline's resume path to a bare existence
  check, no re-derivation.** Trust that the manifest entry for an
  already-produced output was correctly pushed by whichever run created
  it, and rely on the shared upsert-by-name manifest merge (every batch's
  own fresh entries overlay onto the persisted `manifest.json`, never
  wiping entries a *different* run already wrote) to keep the aggregate
  manifest complete across many separate invocations.
- **If a genuine schema change requires refreshing already-decoded items'
  metadata**, do it as a one-time, explicit, opt-in migration pass (a
  separate flag/script, or simply deleting the stale outputs so they get
  freshly re-decoded) — not as a standing per-resume cost every ordinary
  batch pays forever.
- **If cheap in-process re-derivation is genuinely available** (e.g. a
  small already-parsed header struct, not a subprocess spawn), that's a
  different cost profile than a fresh external process per item and may be
  fine to keep on resume (this is what the texture pipeline this project
  is modeled on actually does) — the bug specifically is spawning a real
  subprocess per already-finished item, not "re-deriving metadata on
  resume" in the abstract.
