# A generic sprite-gallery component silently mis-renders a manifest missing `width`/`height`

**When it bites:** pointing a reusable atlas/sprite-gallery UI component (in
a `www/` docs site, the offline asset viewer, or any other consumer built
against the project's generic `AtlasMeta`-like convention — `{ frames:
[{name,x,y,w,h}], width, height }`, per this agent's own Output Conventions)
at a manifest JSON that was authored for a *different* set of consumers, and
every card/cell renders as the whole sheet tiled small instead of its one
cropped frame — with zero console error.

Confirmed root cause: a project's own asset-pipeline script
(`buildIcons()`) wrote a richer, purpose-specific manifest shape
(`{ iconSize, columns, rows, army, portraits, frames }`) for its existing
consumers (a nibble-decode entity-icon mapper, a Node export script), which
never needed top-level `width`/`height` and so never got them. A later,
independently-written gallery component assumed the generic `AtlasMeta`
shape and computed CSS `background-size` as `` `${manifest.width * scale}px
...` ``. `undefined * scale` is `NaN`, and `background-size:
"NaNpx NaNpx"` is a value the browser treats as **invalid and silently
drops** — no exception, no warning — falling back to the image's native
size. The frame crop positions were computed assuming the *scaled* size, so
every card ends up showing the entire sheet at native resolution,
mispositioned.

**The generalizable trap:** a shared/generic UI component's assumed input
shape is a convention, not a type-checked contract, when the producer and
consumer are separate scripts in the same monorepo with no shared TS
interface between them (a `.json` file has no compile-time shape check). A
manifest can look completely reasonable — correct `frames` array, sane
per-cell `x/y/w/h` — and still silently fail a generic consumer over one or
two *missing* top-level fields nobody thought to add because the manifest's
original, narrower set of consumers never needed them.

**The fix:** when a card/cell shows the whole atlas instead of one cropped
frame, check the manifest for the exact top-level fields the component's
size/position math reads (`width`/`height` here) before suspecting the
per-frame data or the image file. Add the missing fields at the producer
rather than special-casing the consumer — this keeps the manifest a true
`AtlasMeta` superset other future consumers can also rely on. More broadly:
whenever adding a new consumer of an existing project manifest, diff its
assumed shape against the actual JSON keys before writing render logic
against it, rather than after debugging a rendered mis-crop.
