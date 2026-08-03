# A musashi-harness "PC left the engine's code range" stop condition can be defeated by the engine's own cleanup code

**When it bites:** running a game's own decompression/decode routine under
a musashi (or similar) emulator harness with no real OS/library environment
behind it, using "stop once PC leaves [engine_start, engine_end)" as the
completion signal, and the run appears to hang indefinitely (same PC values
recurring, registers that look frozen) even with a very large cycle budget.

Many Amiga-executable decompression engines end with a small piece of
runtime-environment-aware cleanup before their final `RTS` — e.g. reading
`ABSEXECBASE` and conditionally calling a library function (a cache-flush,
a version check) once the real work is done. A minimal harness has no real
Exec/library memory mapped, so that final check reads garbage (typically a
null/zero `ABSEXECBASE`), and the code it "calls" or branches to can be
unmapped memory that the harness's read functions return as all-zero bytes
— which decode as real (if degenerate) 68k instructions. The CPU then
executes that garbage for a while and, because zero-filled "code" often
loops or lands back near address ranges that happen to alias the engine's
own loaded location, can wander right back inside `[engine_start,
engine_end)` with completely unrelated register state.

Confirmed on Conan the Cimmerian (Amiga): a harness watching "PC left the
512-byte engine's code range" hung for a full 4-billion-cycle budget,
showing what looked like a genuine infinite loop — the exact same 5
addresses cycling, with one register frozen at a single value and another
oscillating between two nearby values, sampled every 2,000,000 cycles.
Resampling with a **different, non-round cycle stride** (1,300,003 instead
of 2,000,000) immediately showed real forward progress through the *entire*
run — the apparent hang was a stroboscopic artifact: the harness's sampling
interval happened to be a near-exact multiple of the wander loop's own
period, so every sample caught it at (almost) the same phase. The real
completion point (verified independently) was ~30 million cycles in, a tiny
fraction of the 4-billion-cycle budget that had been "exhausted."

Two independent, complementary fixes:
1. **Never trust a single fixed sampling stride when diagnosing an
   apparent emulator hang.** If register state looks frozen, re-sample at a
   deliberately different, non-round interval before concluding it's a real
   infinite loop — an aliased stroboscopic read is indistinguishable from a
   genuine hang using only one stride.
2. **Don't gate completion on PC leaving the engine's address range at
   all.** Watch a register the algorithm itself uses as its own completion
   signal (a pass counter, a "done" flag) and stop as soon as it reaches
   its known terminal value, plus a small fixed flush margin — this is
   immune to whatever the engine's post-completion cleanup code does,
   because it never depends on where the CPU ends up wandering afterward.
