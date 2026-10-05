# A shared landing instruction (crash PC, or a doc's own address citation) doesn't pin which path reached it

**When it bites:** A crash log's PC (or a static trace's cited "failure
address") lands on a function's shared return/cleanup/epilogue block, and
that block is reachable from **more than one branch that isn't a shared call
chain** (i.e. not just "several call sites `bl` into one subroutine" —
several *internal* `b`/`b.cond` edges from unrelated parts of the same
function land on the identical instruction). Before tracing "the" call chain
or subsystem that reaches it, check whether a *different*, earlier, cheaper
validation check can jump straight there too.

The same trap fires with no crash at all: a doc cites a specific address as
"where behavior X happens" for an already-disassembly-confirmed mechanism
(a state machine, a dispatcher), and that address is a **shared write-back
site** several of the mechanism's own branches converge on to store their
result — not the actual per-branch test the prose describes. The citation
looks plausible (it's a real instruction, inside the right function, doing
something related) right up until you check what it actually reads.

## What went wrong

Fire Emblem: Three Houses (Switch, `chimera`): a Ryujinx crash log reported
`PC = main+0xa3418c` inside a native `_M1G`/G1M block-parser function
(`main+0xa33bd0`). That address is the fall-through of a shared
failure-cleanup block (`main+0xa34168`-`0xa3418c`) that makes two virtual
(`blr`) calls and is reached from **eight** different subsection-handler
failure branches deeper in the function (LLOC/ONUN/VNUN and others). Two
full passes — mine, then most of a `re-codebreaker` escalation before it
found the real answer — assumed the reported PC meant execution had reached
that cleanup block via one of those eight subsection-handler branches, and
spent real effort tracing which handler (LLOC? ONUN? VNUN?) was failing on
real data. Wrong subsystem entirely.

The real path: a much earlier, unrelated check — a block-level `"_M1G"`
magic-number comparison, `cmp w8,w9; b.ne main+0xa3418c` at
`main+0xa33c4c`/`main+0xa33c50` — branches **directly** to the identical
landing PC, completely bypassing the cleanup block's two `blr` calls. It's
disjoint from the subsection-loop failure paths; it just happens to target
the same address because both are simply "the function's NULL-returning
exit."

## The fix

**Derive every register in the dump from its own last-write instruction,
specifically along each *candidate* path to the reported PC** — not "the
path that's semantically closest to the crash's apparent symptom." In this
case `X8=5` (the literal first word of the injected file's non-G1M payload,
loaded by the magic check itself at `main+0xa33c3c`), `X20=0` (zeroed by an
unconditional `mov x20,xzr` a few instructions before the magic check, never
touched again on this path), and `X9="_M1G"` (synthesized at the magic
check via `w23+0x19`) only make sense on the magic-check path — on the
cleanup-block path they'd hold different, incompatible values (`X20` would
be a non-null block pointer, `X8` would come from a `blr`'s return). Building
this register-by-register account for **each candidate path** and checking
which one is internally consistent identifies the real path in one pass,
without tracing any subsystem "near" the PC by feel.

General form: a debugger/crash-log PC pinpoints an *instruction*, never a
*path*, whenever more than one control-flow edge reaches that instruction.
Treat every register value as independent evidence to be re-derived per
candidate path, not as corroboration of whichever path you already assumed.

## Second instance: a doc citation, not a crash

Valkyrie Profile (PSX, `valkyrie`): `dungeon-field-mechanics.md` documented a
4-state double-tap-dash detector (`0x80068094`) from a real disassembly
pass, including a byte-verified excerpt of its state-dispatch header — but
one further claim, "the dash-control sense is inverted by `ctx+0x3c0 & 0x40`
at `0x800682a0`/`0x80068304`," was never independently re-checked. A round-207
rigor-audit re-disassembled the whole function fresh and found neither
cited address reads `ctx+0x3c0` at all: `0x800682a0` is a `lw` of the dash
flag itself inside state 3's *unconditional* release-clear, and `0x80068304`
is an unrelated `and` against the held-direction mask inside a different
state's "is the direction still held" test. Both are real, on-topic-looking
instructions in the right function — just not the test the prose named.

The real `ctx+0x3c0 & 0x40` tests were at `0x80068120` (state 0) and
`0x80068230` (state 2), and re-tracing them surfaced a second thing the
one-line citation had hidden: the doc's table only described state 2
touching the dash flag, but state 0 does too, and the two sites are exact
polarity mirrors of each other (which one SETs vs. CLEARs swaps with the
sense bit). A wrong citation for "where" a claim happens is frequently
paired with the claim itself being incomplete — the citation was never
checked, so neither was the rest of the sentence built on it.

General form, restated for statics: a section can carry ONE real,
byte-verified disassembly excerpt establishing the mechanism's overall shape
credibly, while a separate, more specific claim a few lines later (a config
bit's meaning, a sense inversion, an edge case) cites its own address that
was never independently disassembled. Re-derive every such claim from the
cited address's own bytes before trusting it, even in an already-"confirmed"
section — and when it's wrong, check the surrounding prose for what the
correct site would have shown, not just fix the number.
