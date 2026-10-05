# A shared decode library using Node's Buffer can't run client-side without a polyfill — ship its OUTPUT as a static asset instead

**When it bites:** a project's interactive browser-side viewer/walker
(`tools/walker`, `tools/viewer`, etc.) wants to decode a game format
on-demand at runtime (e.g. to avoid a whole new offline export step), and
the format's existing shared decoder — written for the offline Node
pipeline — uses `Buffer` (`Buffer.from`, `instanceof Buffer`,
`buf.readUInt32BE`, etc.) internally. `Buffer` is a Node global, not a
browser one; calling that decoder from browser-bundled code either throws
outright or (worse, if some other dependency happens to have pulled in a
polyfill) behaves subtly differently. Before assuming a shared `tools/`
decode module can be reused unmodified from browser-side code, grep it for
`Buffer`/`node:*` imports.

## What happened

Ishar's (Amiga AGA) Silmarils "ALIS" script container/codec
(`silmarils-unpack.ts`) uses `Buffer.from(buf.buffer, ...)` and
`instanceof Buffer` internally. A new first-person renderer needed a
location script's DECOMPRESSED bytes inside the browser-side walker
(`tools/walker`), and the project's `vite.config.ts` has no Buffer
polyfill (`vite-plugin-node-polyfills` or similar) configured. Rather than
port the whole codec to be Buffer-free (real risk of introducing a decode
regression in an already-verified, corpus-wide-tested module) or add a
polyfill dependency (a build-config change with its own footprint), the
fix was to add one small Node-side export step that runs the existing,
unmodified decoder once and writes its OUTPUT (the already-decompressed
bytes) to a static binary asset (`public/assets/<game>/<platform>/...`);
the browser then just `fetch()`s already-decoded bytes with zero
client-side decompression logic at all.

This is also just the seer-framework architecture's own rule stated
concretely ("the pipeline decodes; the browser only ever consumes
preprocessed output") — the mistake this lesson guards against is reaching
for the shortcut of calling the Node decoder directly from new browser code
without checking it against that rule first, especially when the decoder
in question already exists and "just importing it" looks like less work
than writing a new export step.

**Generalizes to:** any shared `tools/shared/*` decode/decompression module
being reused by a new browser-facing consumer for the first time — check for
`Buffer`, `fs`, `node:*`, or other Node-only APIs before wiring it in
client-side, and default to "ship the decoded output as a static asset from
the existing Node pipeline" over "port the decoder to be browser-safe" or
"add a polyfill," unless the decode genuinely must happen live in the
browser (e.g. it depends on runtime-only state the offline pipeline can't
know, which is rare).
