# A huge JSON intermediate can hit V8's hard string-length ceiling (~512 MiB); `--max-old-space-size` does not help

**When it bites:** a Node.js pipeline stage writes/reads a large per-file
JSON intermediate (decoded vertex/sample/record data for one big
container — a whole open-world scene, a giant archive entry) and a
`readFileSync(path, 'utf8')` or `JSON.stringify()` throws `Error: Cannot
create a string longer than 0x1fffffe8 characters` / `code:
'ERR_STRING_TOO_LONG'`, especially right after trying to fix it by raising
`--max-old-space-size` and having that make no difference.

## What went wrong

Fire Emblem: Engage's mesh-export pipeline (`chimera` project) wrote one
JSON intermediate per Unity Addressables bundle. Nearly all bundles are
small (one character, one prop), but a handful are whole scene dumps —
`fe_scenes_hub_solanel` alone packs 6,462 static meshes into a single
bundle — and its JSON serialized to ~660 MiB of text. Loading it with
`readFileSync(path, 'utf8')` failed immediately with
`ERR_STRING_TOO_LONG`, not a heap-exhaustion crash. `0x1fffffe8` =
536,870,888 — V8's hard maximum `String` length (~512 MiB of UTF-16 code
units), a fixed engine constant with no runtime flag to raise it.
`--max-old-space-size` controls the *heap size* budget, which is a
different limit entirely; raising it (tried up to 8 GiB) had zero effect
on this failure.

## The fix

Split the source data across multiple output files before serialization,
each kept under a size estimate comfortably below the ~512 MiB ceiling
(this case used a conservative ~150 MB-of-text threshold, computed via a
cheap per-record float/int count estimate rather than repeatedly calling
`JSON.stringify` to measure exactly). Each part carries whatever shared
header/metadata the original single file had (here: the bundle's skeleton
data, cheap relative to vertex data, repeated in every part rather than
factored out) so every part file is independently valid and can be
processed — in this case, exported to its own GLB — without needing to be
reassembled first.

**General principle:** when a Node.js process fails on an unusually large
single string (a whole-file read, a big `JSON.stringify`, a giant
in-memory buffer coerced to a string), check whether the failure is
`ERR_STRING_TOO_LONG` specifically before reaching for a heap-size fix —
`--max-old-space-size`, `--max-semi-space-size`, and similar heap flags
are all irrelevant to this ceiling. The only fix is architectural: don't
produce one string that large. This is also a useful early-warning signal
that a "one JSON blob represents one game asset" pipeline design has hit a
genuine outlier (a whole-scene dump masquerading as a single per-asset
container) worth handling as its own case rather than just working around
the symptom.
