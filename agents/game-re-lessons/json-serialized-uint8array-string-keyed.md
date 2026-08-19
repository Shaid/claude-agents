# JSON-serialized Uint8Array becomes a string-keyed object

**When it bites:** a pipeline decodes binary tables to JSON for browser
consumption (`JSON.stringify`) and a decoded field is a `Uint8Array` (roof
bitmaps, flag bytes, raw pages). `JSON.stringify(new Uint8Array([240, 0]))`
produces `{"0":240,"1":0}` — a plain object with **string keys** — NOT an
array. Any downstream loader that treats the field as an array gets
`undefined` (a bare-array field misread as `{screens}`), an empty array
(`Uint8Array.from(obj)` with no length), or NaN — usually as a silent
promise rejection whose error is masked by a UI loop that overwrites the
status text, so it looks like "the load never happened" with zero console
errors.

**The fix / the tell:** before writing a decoded-JSON consumer, dump the
actual serialized shape of every `Uint8Array` field (`type()` in Python
after `json.load`, `Array.isArray()` in JS). Consume with
`Uint8Array.from(Object.values(obj))` (JS objects iterate integer-like
string keys in ascending order). And when debugging "loader hangs with no
error", check for a swallowed rejection — a `selectGame`-style async flow
whose `.catch` writes a status that a periodic re-render immediately
overwrites makes the failure invisible.

**Confirmed on:** the crawl MM1/MM2 walker wiring (2026-08-14): MM2's
decoded `attrib.json` `roofBits` (a Uint8Array) serialized as a
string-keyed object, and `map.json` was a bare array not `{screens}` —
both made the MM2 loader reject silently; the status stayed on the MM1
game's last render because the animation loop re-rendered over the "load
failed" text every 120 ms. Only an explicit `unhandledrejection`/
state-hook probe revealed the loader never completed.
