# A common-byte-pattern function-prologue census can find a fall-through, not a function

**When it bites:** you've byte-scanned a binary for a common function-start
idiom (e.g. 68k `PHB;PHK;PLB`, or any short "save bank/registers" prologue)
to enumerate candidate subroutine entry points cheaply, and one of the hits
has **zero callers** under every xref/call-site search you try (literal
JSR/JSL to its address, and a scan for its address as a bare pointer-table
entry) — especially if you're about to conclude it must be reached via an
unresolved *indirect* call and go hunting for that call's dispatch table.

## What went wrong

Tracing Urban Strike SNES's boot code, a ROM-wide census for the `PHB;PHK;
PLB` byte sequence (a real, common function prologue in this binary — every
*other* hit checked that session was a genuine callable entry) found 19
matches. One of them, `$A8:EDFB`, looked like a promising "generic raw
tile-blit primitive" — a self-contained, parameterised DMA loop reading its
inputs from zero-page variables. No JSL/JSR to its address existed anywhere
in the 2 MB ROM (checked both as a literal far-call operand and as a bare
16-bit pointer-table entry, in case it was reached via the standard 65816
"push bank, push addr-1, RTL" indirect-far-call idiom). This was written up
as an open question: "generic primitive, unresolved indirect caller."

A `re-codebreaker` escalation found the real answer: `$A8:EDFB` is not a
function at all. It's reached by **fall-through** from `$A8:EDF9`, mid-way
through the tile-upload tail of a much larger routine (`$A8:ED25`) whose
own logic happens to include a mid-body bank switch that is byte-identical
to the same three opcodes used everywhere else as a genuine prologue. There
is no caller to find because nothing calls it directly — it only ever
executes as a continuation of the code immediately before it.

## Fix

A common-prologue byte-pattern census is a cheap **candidate** generator,
not a confirmed function list. Before trusting any one hit — and
especially before spending effort hunting for a "missing" indirect caller
— check whether normal, straight-line disassembly of the *preceding* few
dozen bytes flows directly into the candidate address with no intervening
unconditional control transfer (`RTS`/`RTL`/`RTI`/unconditional `JMP`/
`BRA`). If it does, the "prologue" is coincidental fall-through-reached
code, not a real entry point, and a "zero callers found" result should be
read as "this probably isn't independently callable," not "the caller must
be indirect." Cross-validate every prologue-census hit against at least one
of: a real caller found by xref search, or disassembly of the immediately
preceding bytes showing an actual function boundary (a prior `RTS`/`RTL`
right before it) — don't accept the byte pattern alone as proof.
