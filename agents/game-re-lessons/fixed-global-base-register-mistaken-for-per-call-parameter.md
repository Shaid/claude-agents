# A "which entity" register loaded from a fixed global at function entry may not vary per call at all

**When it bites:** a per-frame draw/update/dispatch function has a local
struct-typed register (often given a generic name like "actor"/"obj"/
"entity" in your own notes, matching a documented struct that genuinely
has per-instance semantics elsewhere) whose fields feed a formula you're
about to describe as depending on "whichever object is currently being
processed" — before trusting that framing, check whether the register's
base address is loaded from a **fixed global at function entry** (not an
incoming argument, and not reassigned inside a visible loop) rather than
being parameterized per call.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 213: a field-sprite
renderer's flags-construction formula reads `actor+0xee`/`actor+0xb8`/
`actor+0x1c`/`actor+0xf6` from a register (`s2`) that a prior round's own
disassembly had implicitly treated as "the entity whose part is being
drawn." Re-tracing `s2`'s provenance found it is set exactly once, at the
function's very first instructions, from `*(0x8007f0e4) + 0xc8` —
`*(0x8007f0e4)` being the confirmed 96-actor array's own **base** pointer,
so `s2` is always **actor slot 0's** own `+0xc8` field, never an
argument-supplied "current entity." Two cheap static checks settled it
decisively rather than leaving it a guess: (1) a whole-overlay literal
`lui 0x8008`+offset census found **zero writers** anywhere to
`*(0x8007f0e4)` (144 readers, 0 writers) — the global genuinely never
changes, so this reading cannot vary call to call; (2) a literal `jal`
caller census for the enclosing function found **exactly one caller**, in
a flat once-per-frame dispatch list with no surrounding loop — consistent
with the function running once per frame using a fixed reference slot, not
once per drawn entity. The correct reading is that these fields are actor
SLOT 0's own state (a reserved/special engine slot with its own
already-documented distinguished treatment elsewhere in the same VM),
making the mechanism a **whole-screen transform toggle** (e.g. a scripted
screen-spin/zoom cutscene effect) rather than a per-character one — a
materially different semantic than "per-drawn-object," reached from the
same disassembled bytes just by tracing one more register.

**Fix:** whenever a struct-typed local you're about to call "the current
X" is set near a function's entry, trace that specific instruction (not
just its type/shape) back to its own source. If it's a `lui`+`lw` (or
equivalent) load from a fixed global rather than a register the caller
supplied, don't assume the global's value varies call to call — run a
whole-file literal-address writer census on that global (cheap: a few
lines of code, works on any fixed-width ISA) and a literal-call-target
census on the enclosing function itself. Zero writers to the global, plus
a single caller with no wrapping loop, is decisive: the register is a
permanently-bound identity, not a per-call parameter, and every field read
through it inherits that same fixed identity — reframe the whole
mechanism's semantics accordingly rather than patching the field-level
formula in isolation.
