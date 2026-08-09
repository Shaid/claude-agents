# Real call/jump targets landing inside a supposedly off-limits region mean your region boundary is wrong, not that the targets are anomalous

**When it bites:** a structural model divides a data/code blob into a
"reserved/header/table" region followed by a "real content" region — based
on an early guess, a superficial byte-pattern resemblance, or an
un-reverified prior pass — and you find one or more real, otherwise
well-formed call/jump/goto targets that resolve *inside* the supposedly
reserved region. The instinct is to write this off as a one-off anomaly,
dead code, or a decode bug in the specific instruction, and keep the
region-boundary model unquestioned.

When several *independent* real targets (not just one, which could be
coincidence or a genuine dead branch) land inside a region you believe is
off-limits, and every one of them decodes to a plausible, in-context
instruction when read as ordinary content rather than being treated as
invalid, that is itself strong evidence the boundary model is wrong — not
that the targets are broken. A boundary you inferred from pattern-matching
alone (the region "looks like" a table because its bytes have a recognisable
shape) is much weaker evidence than a single traced initialization
instruction that sets the real starting value used to address into it.

Confirmed on Spirit of Excalibur's FSME bytecode VM (`middilgard` project):
a prior pass's doc described the first 64 bytes of every entity-class's
bytecode block as a "16-entry native dispatch table, separate from the
bytecode" — inferred because those 64 bytes are almost entirely `0x64xx`-
shaped words (which happen to *also* be the real "goto" opcode's encoding,
a coincidence the earlier pass read backwards as "table of code
addresses"). Several real bytecode `Goto`/`Call` targets, found while
tracing entity behaviour scripts, resolved to word indices inside this
"reserved" 32-word region — initially treated as an anomaly. The actual
fix came from finding the one instruction that sets a fresh object's
starting program-counter value (`_GetObject`'s `CLR.B 39(A0)` — "new
object's PC field = 0") and recognising that 0 is the very first word of
the *entire* class block, not word 32 past a reserved header. There never
was a separate table — the leading run of `0x64xx` words is itself
ordinary, executable bytecode (a bank of goto trampolines, one per
external entry point), and every previously-"anomalous" target was a
completely ordinary jump into it. This was independently corroborated by a
different session's sibling-game module reaching the identical structural
conclusion from scratch.

**Fix:** when real, otherwise-valid addressing keeps landing where a
region-boundary model says it shouldn't, prioritize finding the
instruction that sets the *starting value* of whatever register/counter/PC
is used to address into the structure (an initialization or spawn routine
is the highest-value place to look) over re-examining the individual
"anomalous" targets one at a time. A region boundary inferred purely from
a byte-pattern resemblance is a hypothesis, not a fact, until something
that actually establishes the addressing origin has been traced.
