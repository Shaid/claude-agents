# A ported CPU opcode written as one expression can read a mutating register before a same-expression side effect updates it

**When it bites:** porting a real CPU core's opcode semantics to JavaScript
(or any language with left-to-right operand evaluation and no argument-
evaluation-order guarantee across statements), where an opcode's own
effective-address or branch-target computation needs **both** a register
that a helper function mutates as a side effect (e.g. `fetch8()`
advancing `PC`) **and** that same register's *value* in the same
expression.

Writing the opcode as a single expression — `this.pc = (this.pc +
offset(this.fetch8())) & mask` — silently reads `this.pc` **before**
`fetch8()`'s side effect (advancing `pc` past the operand byte) takes
effect, because `+`'s left operand evaluates first. The bug is invisible
by inspection (the code reads naturally, "current PC plus the fetched
offset") and produces a *consistently* wrong result exactly one operand-
byte short, every single time that opcode runs — not an intermittent or
edge-case failure. Confirmed on a from-scratch SPC700 core (`ceres`
project, FFVI SNES): a single-opcode `BRA` (unconditional relative branch)
implementation had this exact shape while every *other* relative-branch
opcode in the same file (`BEQ`/`BNE`/`BBS`/`BBC`/`CBNE`/`DBNZ`) happened to
pass the fetch as a function-call **argument** (`this.branch(cond,
this.fetch8())`), which evaluates the argument (running the side effect)
before the callee's body reads `this.pc` — so only the one differently-
shaped opcode was affected. 20 hand-computed instruction-execution unit
tests (this project's own standard rigor) did not catch it, because none
of them happened to specifically exercise `BRA` with a hand-verified
target address — the bug survived an otherwise-solid test suite simply
because no test asked the one question that would have caught it.

**Real-world consequence, worth internalizing**: this class of bug doesn't
crash or produce garbage — it silently sends the program counter to a
plausible-looking, in-bounds, real-code address one byte off from the
intended target, so downstream execution *looks* like it's running
normally (jumps that happen to fall through to real code, real registers
getting written, real output being produced) while actually executing an
entirely different, un-intended code path. On the confirmed case, the
mis-landed PC happened to fall mid-instruction into unrelated driver code
that coincidentally walked back to the correct main loop a few
instructions later — meaning the desync self-healed every single time it
occurred, leaving no state corruption *except* whatever real work the
skipped-over target instruction was supposed to do (here: an entire
per-tick scheduler call, silently never made). This is the kind of bug a
"does the emulator run without crashing / does register state look
plausible" check will never surface — only a byte-exact disassembly-vs-
execution cross-check (comparing a live PC trace against a real listing
line by line) or a targeted, hand-computed unit test for the exact opcode
finds it.

**Fix, and general defense**: for any opcode whose real semantics need a
register's value *after* a fetch's side effect, sequence the fetch into a
local variable explicitly (`const rel = this.fetch8(); this.pc = (this.pc
+ offset(rel)) & mask;`) rather than inlining the fetch call into the same
expression that reads the mutated register — this makes the ordering
require no reader-side knowledge of JS operand-evaluation rules to get
right. When porting a CPU core, audit every opcode handler for this exact
shape (a fetch-with-side-effect call appearing in the same expression as a
read of the register it mutates) as a dedicated pass, not just individual
opcode-by-opcode unit tests — a single audit catching one instance across
a whole opcode table is cheaper than relying on hand-computed tests to
happen to exercise the specific opcode where it occurs.
