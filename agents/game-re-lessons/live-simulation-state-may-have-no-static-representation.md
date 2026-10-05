# A live simulation-state array (entities, AI, physics objects) may have no on-disk representation at all — the deliverable is a memory-layout doc, not a decoder

**When it bites:** a task asks you to "find the entity/unit/actor data
structure" or "reverse-engineer the AI/simulation state" for a game, phrased
in the project's usual format-RE shape (find it, write a decoder + extractor,
ship assets) — especially when the project's convention is "decode a format,
build a pipeline stage, ship JSON/PNG."

Most of this agent's targets are genuinely on-disk: sprites, maps, palettes,
audio all live in a file somewhere, get depacked, and get a decoder + a
`tools/`-side extractor per the standard pipeline shape. **Live entities in a
running simulation are different in kind**, not just in size: the array a
game's per-tick logic walks (unit positions, AI task state, animation phase
counters) is typically allocated and zeroed by the game itself at map-load
time, in a RAM region that sits entirely outside the loaded executable/data
image. There is no file anywhere in the data directory that contains this
array's contents — it doesn't exist until the game runs, and it's gone the
moment it exits (barring a save-game format, which is a genuinely different,
separately-loadable thing).

Confirmed on PowerMonger (Amiga): the entity pool (231 literal-address
references throughout `RUN_PROG`, easily the most heavily-touched data
structure in the binary) lives at a fixed address (`$77B7A`) that falls
**outside** the 110804-byte loaded program image (`$1400`–`$1B054`) — same
as the already-known terrain height/mask buffers. Every field offset, every
dispatch-table entry, every back-reference was recovered by reading what
*code* does at that address (loads, stores, comparisons, jump-table
dispatch) — never by reading bytes *at* that address, because there are none
in any static file to read.

**The fix:** when a target turns out to be a runtime-only buffer like this,
don't force the standard "decode this format" deliverable shape onto it —
there's no format to decode, only a memory layout to document from
disassembly (field offsets, dispatch-table addresses, confirmed access
patterns) plus explicit "hypothesis" labels wherever code sites disagree
or weren't fully traced. Producing a `docs/<game>/<platform>/*.md` writeup of
the *layout* (with disassembly citations for every field) is the correct,
complete deliverable — not a stalled attempt at a `tools/` extractor script
that has no input file to run against. A follow-up session's path to
*verifying* any of it is live-capture (savestate/debugger memory read), not
a static-file oracle — flag that explicitly as the open next step rather
than as a failure of this session's work.

Related: `runtime-only-value-often-static.md` makes the opposite-shaped
point for a *single value* (don't assume live capture is needed before
exhausting static tracing) — that doesn't contradict this lesson, which is
about a *whole array of per-instance mutable state* that is structurally
runtime-allocated (confirmed by its address falling outside the image), not
about a single computed constant that might turn out to be a static table
lookup after all.
