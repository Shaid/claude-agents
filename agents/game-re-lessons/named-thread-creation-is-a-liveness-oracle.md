# A named OS thread-creation call site is a cheap, strong liveness oracle — the mirror image of the gating-argument-constant pitfall

**When it bites:** a candidate "is this really live" mechanism (a producer/
consumer pair, a per-frame job queue, a subsystem entry point) has real
callers under `xrefs_to`, but you want stronger evidence than call-graph
presence before calling it confirmed-live — especially right after (or
instead of) hunting for a gating-argument trick that could make it dead
code (see `gating-argument-may-be-a-compile-time-constant-not-data.md`,
its exact mirror image).

**The technique.** Engine code routinely names its own worker threads for
debugging: `CreateThread(obj, entryFn, "SomeSubsystemThread", priority,
affinity, stackSize)`. That literal string is trivially findable (`strings`
on the binary, or a plain string-table scan), and its one xref hands you
the thread-creation call site for free — which in turn hands you the entry
function pointer as a literal operand, not an inferred one. If that entry
function is (or calls into) the mechanism you're checking, you have
end-to-end proof the OS itself was told to run it, independent of any
static call-graph reasoning about who else might call it. This is strictly
stronger than "found N callers via `xrefs_to`" for the specific question
"does this code path execute at all" — a called-but-argument-gated-dead
function can still have real callers (see the constant-gate pitfall this
file mirrors), but a function named and handed to a live OS thread creator
has no equivalent silent off-switch to check for.

**Worked example.** Fire Emblem: Three Houses (`chimera` project,
2026-08-26): a suspected dead pointer-table entry
(`main+0x1965950`) turned out to have exactly one reader in the whole
image, found via an ADRP-pair reference scan over `.text` — a
thread-creation call site (`main+0x21B7C`) that loads the entry, then
immediately loads the literal string `"ApplyMotionThread"` (found at
`main+0xC4DE2B`) as the thread's name argument, then calls the engine's
`CreateThread`/`StartThread` wrappers. The named entry function turned out
to be the enclosing function of the exact consumer loop under
investigation (the `RealtimeRig` pose-operator job-queue dispatcher),
upgrading a much weaker "likely a genuine per-frame/per-tick system
(suggestive, not proof)" call-graph-only finding to fully confirmed-live —
by a completely different and much stronger mechanism than the pointer-
table adjacency the earlier framing had rested on.

**Practical notes:**
- Look for the thread-naming string near known OS thread-creation wrapper
  functions (a small handful of call sites store a name pointer, a
  priority word, an affinity mask, and a stack-size constant in a fixed
  argument shape — that shape itself is a good search anchor even before
  you have a specific string).
- The technique generalizes past thread creation to any API that takes a
  literal debug name alongside a function/object pointer (job-queue
  registration, RTTI-style class-name tables, asserts that print a
  subsystem name) — anywhere the engine embeds a human-readable label next
  to the thing you're trying to prove is live.
