# A decompiler's "inherited/undefined register parameter" (`in_A0`-style) is not proof no visible load exists — read the raw instructions at the function's real entry

**When it bites:** a decompiled function shows a register (e.g. Ghidra's
`in_A0`/`in_r0`/`in_EAX`) as an inherited-from-caller input with no
dataflow shown for it, and the conclusion drawn is "this value's origin is
further up the call stack, untraceable from here without more context" —
especially when that conclusion then blocks answering a specific "where
does pointer/base X come from" question. This is a narrower, more specific
trap than `forced-function-boundary-decompile-misreads-role.md` (which is
about the decompile starting at the *wrong* address entirely) — here the
function boundary is correct, but the decompiler's high-level C view still
elides real information.

Confirmed on Midwinter (1) (Amiga, `hunter`, via a `re-codebreaker`
escalation): the brief handed to the escalation stated, as an established
premise from a prior pass, "A0 is never visibly loaded in this function;
it must be inherited from further up the call stack" — based on Ghidra's
decompiled C showing `in_A0` with no assignment. This was simply false.
The function's *second instruction*, plainly visible in the raw
disassembly at its real entry point, was `movea.l ($0000ff22).l,A0` — a
literal absolute-address load the decompiler's C-level output had folded
into a generic "inherited parameter" annotation rather than surfacing as
a load. That one instruction, once read directly, immediately named the
grid base pointer, cell stride, and index formula the whole terrain-
renderer trace needed — work a prior pass had marked as blocked on
"further up the call stack" when the answer was one instruction into the
function everyone already had open.

**Fix:** whenever a decompiler shows a register as an inherited/opaque
input with no visible producer, don't accept that as proof no producer
exists in this function — dump the raw instruction listing starting at
the function's confirmed real entry point and read the first several
instructions by hand. A decompiler's job is to produce plausible-looking
high-level C, and folding "this register happens to already hold a value
when this basic block starts" into a bare inherited-parameter annotation
is exactly the kind of simplification that can silently discard a literal
load the raw bytes still contain. This costs seconds and should be routine
before writing "value X has no traceable origin from here" into a report.
