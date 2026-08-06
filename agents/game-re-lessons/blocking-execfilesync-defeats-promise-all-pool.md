# `execFileSync`/synchronous subprocess calls silently defeat a `Promise.all`-based concurrency pool

**When it bites:** a Node.js/TypeScript pipeline shells out to an external
tool (umodel, an emulator core, a compressor CLI) once per file/object in a
batch, wrapped in a `runPool`-style worker pattern (`Array.from({length:
concurrency}, async () => { while (items left) await fn(next item) })` +
`Promise.all`) — and the docs/commit message claims a "large real speedup"
from concurrency, but nobody has actually timed it against the sequential
baseline.

Node.js is single-threaded for JS execution. `child_process.execFileSync`
(or any other genuinely synchronous subprocess call) blocks that one thread
until the child process exits — including blocking every other "concurrent"
`async` worker's own turn to even *start* its own child process, since
they're all cooperatively scheduled on the same thread. The `async`/`await`
syntax around the call is cosmetic when the function being awaited isn't
actually asynchronous (`execFileSync` returns a plain value, not a
`Promise`) — the `runPool` pattern still *looks* concurrent and the code
still runs correctly, it just doesn't get any faster than raw sequential
execution.

Confirmed directly on Drakengard 3 (PS3, `flower` project) while sizing a
~16,000-invocation per-object `umodel -export -gltf` mesh-conversion pass:
a `runPool`+`execFileSync` reproduction of the project's existing texture-
export pattern measured **~8.06 wall-clock seconds for 8 "concurrent"
1-second child processes** (`sleep 1`) — essentially the fully-sequential
8 seconds, not the ~1 second real parallelism would give. Switching to
`child_process.execFile` (or any other genuinely non-blocking spawn API)
wrapped with `node:util`'s `promisify`, under the identical `runPool`
harness, measured **~1.02 seconds** for the same 8 processes — confirming
both the diagnosis and the fix in one before/after pair. The existing
texture-export pass (which used the synchronous version) had still
produced correct output over a prior session (61,244 real PNGs) — the bug
is purely a wall-clock/throughput regression, not a correctness one, which
is exactly why it went unnoticed: the pipeline "worked," just slower than
its own comments claimed.

**The fix**: use `child_process.execFile` (or `spawn`) + `promisify`
instead of `execFileSync`/`spawnSync` inside any `Promise.all`-based worker
pool. If a synchronous variant already exists and is depended on elsewhere
(a test suite, a caller wanting synchronous semantics), add the async
version alongside it rather than converting in place — don't assume every
caller of the synchronous version also runs inside a concurrency pool.

**The general check, before trusting a "concurrency-pooled, large real
speedup" claim in any doc or comment**: time a small worker-pool repro
against a `sleep N` (or equivalent trivially-parallel) child process command
directly — a few seconds of measurement settles it definitively, and is
far cheaper than discovering the regression by having a big batch job take
several times longer than expected.
