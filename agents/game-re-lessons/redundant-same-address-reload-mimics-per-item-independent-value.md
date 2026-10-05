# Code that reloads the identical struct field once per usage site can look like N independent per-item values — check the load ADDRESS, not the load COUNT

**When it bites:** a disassembled loop/block does the same
load-modify-store sequence N times in a row (once per corner/channel/
element of a small fixed-size set), and each occurrence re-issues its own
`lw`/load instruction from the same base register+displacement rather than
reusing a value already sitting in a register from an earlier occurrence —
tempting a "per-item independent value" label (e.g. "per-corner scale
factor," "per-channel gain") before checking whether every one of those N
loads actually targets a DIFFERENT address.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 212: a field-sprite
renderer's "per-corner scale" render-mode branch was flagged, purely from a
pre-disassembly skim, as dividing each of 4 quad corners by what looked
like 4 independent scale factors — the code visibly reloads a divisor
register from memory (`lw v1, 0xb8(t0)`) immediately before EACH of the 4
divisions, which reads exactly like "fetch this corner's own scale value."
Actually disassembling and running it under a scoped interpreter showed
every one of those 4 loads reads the identical offset (`obj+0xb8`) off the
identical base register (`t0`, never reassigned) — i.e. one shared 32-bit
Q16 divisor, redundantly reloaded 4 times because the compiled code never
bothered to keep it live across the intervening `div`/`mflo` sequence
(which clobbers no general-purpose register the value needed, but the
compiler re-fetched it anyway rather than caching it — ordinary
unoptimized-codegen behavior, not evidence of per-item data).

**Fix:** when N occurrences of the "same-looking" load precede N similar
operations, diff the base register AND the literal displacement of every
one of the N loads before assigning any "per-item independent" semantics.
If they're all identical, the value is shared and reused, not per-item —
the redundant reload is a compiler artifact, not a data-model signal. This
generalizes past MIPS/PSX to any ISA and any compiled (not hand-optimized)
code: never infer "N independent inputs" from "N repeated load
instructions" without confirming N distinct addresses.
