# `@seer-project/pipeline`'s `writeShardedManifest` shards by `entry.category`, not `entry.type`

**When it bites:** wiring a brand-new content type (mesh, texture, a second
audio sub-category, ...) into an existing `buildAssets` pipeline that
already ships at least one other content type through the same
`finalizeManifest`/`writeShardedManifest` call — new entries push a `type:
'mesh'` field (or whatever the new asset kind is called) by pattern-matching
an existing entry's shape, and the pipeline run completes with no error, a
correct total entry count, and correct files on disk.

**Root cause:** `ManifestEntry.type` (`'mesh'`/`'audio'`/`'sprite'`/...)
tells the *viewer* how to render an entry. `writeShardedManifest`'s own
per-category `manifest/<category>.json` splitting keys on a **separate**
field, `entry.category` (defaulting to `'uncategorized'` when absent) — a
project's `CATEGORY_DISPLAY_NAMES` map is looked up by this same field. The
two fields look interchangeable at a glance (both are short lowercase
strings describing "what kind of thing is this"), and nothing in the
`ManifestEntry` interface or the sharder's own success output makes the
distinction obvious: a run with entries carrying `type: 'mesh'` but no
`category` field completes cleanly, writes the right PNG/glTF/bin files,
and reports the right total entry count — only the sharded-manifest summary
line reveals the bug, and only if you read it closely (`(uncategorized=304)`
instead of the intended `(mesh=304)`).

Confirmed on NieR (2010, PS3, `flower` project): a new
`tools/nier/mesh-assets.ts` stage pushed `type: 'mesh'` entries copying an
existing audio-entry's field shape, omitting `category`. `finalizeManifest`
ran without error and `public/assets/nier/ps3/manifest.json` had the
correct 304 entries with correct `gltf`/`bin` paths — but
`writeShardedManifest`'s own log line read `wrote 1 category shard(s) ...
(uncategorized=304)` instead of using the project's newly-added `mesh:
'Character/Weapon Models'` display name, because nothing set `category`.

**The fix:** when adding a manifest entry shape for a pipeline stage
you haven't shipped from this project before, don't copy an existing
entry's fields by pattern-matching — grep the manifest-writing code (or
`@seer-project/pipeline`'s `manifest-sharding.ts` source) for which field
name it actually reads, and set both `type` (viewer rendering) and
`category` (manifest sharding) deliberately. Cheapest verification: after a
pipeline run, read the sharding summary line itself (not just the total
entry count) and confirm every category name is the one you intended, with
no unexpected `uncategorized=N` bucket.
