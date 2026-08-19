# A literal-argument census that only checks instructions adjacent to the call site misses compiler-spilled constants

**When it bites:** hunting for code-embedded literal id/index/offset
arguments to a known call target (a resource loader, a table lookup, a
DMA setup) by scanning for an immediate-load (`addiu $reg,zero,N`/`li`)
either in the call's own delay slot or in the instruction(s) immediately
preceding the `jal`/`jsr` — and the scan comes back with **zero hits**
across a whole binary, including for call sites you have independent
reason to believe use a literal (e.g. the call target is known to be
invoked with a small, plausible constant range).

A too-narrow adjacency window produces a **false negative**, not a wrong
value (contrast `nearest-preceding-immediate-is-not-dataflow.md`, whose
failure mode is the opposite: picking a *wrong* nearby immediate rather
than missing a real one entirely). The compiler routinely computes a
constant, **spills it to a stack slot or struct field** (`sh $reg,OFF(sp)`
right after the immediate load), and only reloads it into the actual
argument register (`lh $arg,OFF(sp)`) at the real call site — which can be
many instructions later, inside a different basic block, and can even
reload the *same* stack slot twice for two different calls in sequence.
None of that is visible to a scan that only looks at the instruction pair
immediately touching the `jal`.

Confirmed on Valkyrie Profile: Lenneth (PSP): a literal-index scan for
`Field_master.prx`'s calls into a shared resource-loading API (`addiu
$a0,zero,N` adjacent to the `jal`) found **zero** hits anywhere in the
binary, including for the two content families with independently
confirmed ground truth (known-good `PSPVAL1.PFS` directory indices for a
loading-screen PNG set and a legacy video pair) — a result that briefly
looked like grounds to escalate "does a literal-index convention exist at
all." Widening the search to also follow `sh $reg,OFF(sp)` (spill)
paired with the matching `lh $arg,OFF(sp)` (reload) at the actual call
site immediately found a real, verifiable example: a runtime-flag-gated
choice between two literal PSPVAL1.PFS indices (`0x87f`/`0x886`), both of
which independently decoded to real, non-degenerate, structured content
when read back from the actual archive.

**Fix:** a literal-argument-provenance scan needs at minimum two passes —
first, the narrow immediate-adjacent-to-call check; second, a
store-then-matching-load chain (same stack/struct offset, same base
register) walked backward from the call site, not just the previous one
or two instructions. Treat an all-zero result from the narrow pass alone
as inconclusive, not as evidence the convention doesn't exist, especially
when a plausible ground-truth example (a call site whose consumer role is
already independently confirmed) exists to test the widened scan against
before trusting either a positive or a negative.
