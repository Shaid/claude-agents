# A single shared LIFO worklist across several independent execution threads can starve some threads' own starting points under a shared budget

**When it bites:** walking a format with several genuinely-independent
parallel execution threads (per-channel/per-voice sequence tracks, per-
object script threads, any "N independently-scheduled streams sharing one
resource pool" shape) via one shared worklist/stack, where each thread's
own internal unconditional jumps get pushed onto that *same* worklist
alongside the other threads' own starting points, under a shared size/byte
budget.

A LIFO (stack, `.pop()`) worklist processes whatever was pushed *last*
first. If thread A's own start is pushed, then thread A's processing
discovers a long internal jump chain and pushes many more items before any
other thread's start is ever popped, a shared budget can be entirely
consumed by thread A's own content before threads B through N's starting
points are reached at all — even though each of those threads is equally
real and equally important. The failure is silent and specific: an
unreached thread doesn't error, it just falls back to whatever default
your harness uses for "target not found" (a null/end sentinel, say),
producing an unambiguous wrong result (a channel that should carry real
content resolving to silence/nothing) with no exception to catch it.
Confirmed on FFVI (SNES)'s AKAOSNES V4 sequence data: with all 8 tracks'
starts and every discovered `GOTO` target sharing one LIFO worklist, a
track independently known to carry real content (not the documented
null-track sentinel) resolved to the harness's synthetic end-stub, because
a different track's own long jump chain, explored first due to stack
ordering, exhausted the shared byte budget before this track's start was
ever popped.

**Fix:** recognize that a thread's own internal unconditional jump is a
*continuation of that same thread's single path*, not a fork creating new,
equal-priority work. Walk each thread's own primary path to completion
first (a simple loop that reassigns the cursor and continues, no worklist
push at all), consuming the shared budget in per-thread-start order,
*before* touching any genuinely optional/secondary content (conditional
branches whose target may or may not ever execute, e.g. a conditional
`LOOP_BREAK`-style jump) — those alone belong on a shared, lower-priority
worklist explored only with whatever budget remains after every thread's
own primary content is placed.
