# A decompile scoped to a mid-function address (a forced/auto boundary at the exact address you queried) yields a plausible but wrong role — re-derive the real prologue first

**When it bites:** a decompiler-derived characterization of a function
("returns a bare bool", "takes no arguments", "is a thin thunk/dead
function") is load-bearing for a verdict, and the decompiled function's
*name is exactly the address you asked about* — especially when that
address is known to be a call site, a branch target, or any address chosen
from a trace rather than from function-boundary analysis.

Ghidra (and IDA) will silently create a function at whatever address the
query lands on if none exists there, decompiling from that point as if it
were an entry. The result is well-formed and internally consistent —
which is what makes it dangerous. Confirmed on Fire Emblem: Three Houses
(`chimera`, Switch, ARM64): `FUN_7100041e44` decompiled as
`undefined8 FUN_7100041e44(void)` with "every path returns 0/1 — an
equipment validation predicate", and that reading misdirected a whole
escalation pass. `0x41E44` is a mid-function `bl` site; the real function
starts at `0x41DE0`, takes two pointer arguments, and its body contains
the decisive evidence the pass was hunting (it recomputes the target value
and asserts equality with a vtable getter). The `(void)` signature was
the tell: the code visibly consumed registers the signature said didn't
exist.

**Tells that a decompile is boundary-artifacted:** the function name equals
the queried address rather than a previously-known entry; a `(void)` or
suspiciously-empty signature while the first instructions read argument
registers; no prologue (`stp x29,x30`/`push ebp`-family) at the claimed
entry; Ghidra flagging the symbol as a "forced" or analysis-created
function.

**Fix:** before trusting any decompile-derived role, re-derive the real
function start independently — scan backward for the nearest
`ret`/unconditional-branch/padding followed by a genuine prologue (a
20-line script; keep one per project) — and decompile from *that* address.
If the two starts differ, everything concluded from the mid-function
decompile is suspect, including "dead code"/"thunk" verdicts on other
addresses from the same pass.
