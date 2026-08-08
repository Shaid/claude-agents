# A `type: "texture"` manifest entry needs its own `.json` atlas sidecar, not just the `.png`

**When it bites:** wiring a *new* pipeline step (a brand-new format decoder,
not an existing shared module like `cavia-pipeline.ts`) that pushes
`type: "texture"`/`"sprite"`/`"screen"` `ManifestEntry` rows with a `png`
field — the PNG itself decodes and looks correct when opened directly, but
the offline asset viewer shows a literal **"Failed to load atlas
metadata"** error state the moment that asset is selected, with **zero
browser console errors** (this is a handled, deliberate error path in
`viewer.ts`, not a crash — easy to skim past in a Playwright screenshot if
you're only checking for console errors).

**Root cause:** the viewer's `sidecarPath(asset, '.json')` derives an atlas
metadata request from the entry's own `png` path unconditionally for every
non-mesh/audio/video/scene asset — it does not treat the sidecar as
optional. A pipeline step that writes only the `.png` (no `.json` next to
it with `{frames: [{name,x,y,w,h}], width, height}`) produces an entry the
manifest schema calls valid (the `ManifestEntry` interface doesn't require
a sidecar to exist on disk, only a `png` string) but that the viewer cannot
actually render. Confirmed on a from-scratch `TIM2`/Chaos Legion+Devil May
Cry texture pipeline (`flower` project): every one of ~8,800 new texture
entries hit this until the fix landed.

**The fix:** any new texture-producing pipeline step must write the atlas
JSON sidecar alongside every PNG it writes, even for a single-frame texture
(`{frames: [{name, x: 0, y: 0, w: width, h: height}], width, height}`) —
copy the pattern from an already-correct producer
(`tools/shared/cavia-pipeline.ts`'s per-texture write) rather than
hand-rolling the manifest push. Cheapest verification: after wiring a new
texture type into the pipeline, actually click one of the new entries in a
live (or Playwright-driven) viewer session — a byte-correct PNG written to
the right path is not sufficient proof the asset is browsable end to end.
