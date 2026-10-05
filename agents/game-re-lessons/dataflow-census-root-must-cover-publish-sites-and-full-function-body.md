# A value-consumer dataflow census is only as complete as its taint ROOTS (loads *and* publish stores of every pointer) and its per-function scan window (to the real function end, not the first `jr ra`) — idiom coverage alone won't save an incomplete root set

**When it bites:** a bias-agnostic register-dataflow census has already been
widened to cover every bit-test/mask idiom you can think of (`andi`,
register-form `and`, `srl`+`andi`, `sll`+sign-branch, etc.) and STILL comes
back with a clean negative for "is this value ever consumed" — before
trusting that negative, check whether the census's own *taint roots* are
complete, not just its idiom coverage. This is a different failure mode
from `narrow-opcode-form-census-false-negative.md` (which is about missing
instruction *shapes* once a value/pointer is already correctly tagged) and
from `struct-field-scan-blind-to-biased-base-pointer.md` (a base register
offset trick) — this is about the census never tagging the right register
as "derived from the target" in the first place, for two specific, easy-
to-miss reasons.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): closing whether a scroll
record's `flags` bit 2 was ever read anywhere took two rounds of
bit-mask-only searches (both false negatives from literal-offset/biased-
base-pointer blindness), then a third round that built a genuinely
idiom-complete census (every `andi`/`ori`/`and`/`or`/`xor`/`nor`/`slti`/
`beq`/`bne`/`sll`+`bltz` form, positively controlled against the confirmed
bit-0/1 tests) — and STILL returned zero bit-2 hits, indistinguishable from
"truly unused" by idiom coverage alone. A `re-oracle` escalation found the
census's root set itself was incomplete in two ways:

1. **It rooted taint only on the pointer's `lw` (load) sites**, tracing
   registers forward from "a `lui`+`lw` that resolves to the confirmed
   global." It never also rooted on the pointer's `sw` **publish** sites —
   the exact moment an installer/allocator writes a freshly-computed record
   pointer back into a global for later use. A record pointer built once
   and cached via `sw $reg, GLOBAL` needs its own re-load of `GLOBAL` to be
   traced as a *second*, independent root; treating only the confirmed
   resolver function's return value and the direct `lui`+`lw` pattern as
   roots missed every consumer that instead re-derives the pointer from the
   cached copy.
2. **It scanned each candidate function only until its first `jr ra`**,
   assuming that ends the function. A function can have multiple exit
   paths (several `jr ra`s guarded by different branches, or a tail that
   continues past what looks like a return inside a delay-slot-adjacent
   sequence); stopping at the first one silently drops any consumer code
   that lives structurally *after* it in the same function body. The fix
   was to scan to the function's real end (the next function's confirmed
   start, from the same prologue/xref census the project already builds
   its function-boundary table from), not the first return instruction
   encountered linearly.

Once both root-completeness gaps were closed, the census was re-run
unchanged in every other respect (same idiom coverage, same positive
controls) and gave the SAME zero-hit result — but now a *trustworthy* one,
because the corpus of registers it considered "possibly holding the target
value" was provably complete rather than merely idiom-complete over an
incomplete set.

**Fix, generalized:** before trusting any "no consumer" verdict from a
register-dataflow census — however many instruction idioms it covers —
audit two things separately from idiom coverage: (a) does it root taint on
every way a pointer/value can enter a register, including a global's own
*publish* (store) sites, not just its load sites (a fixpoint over
loads-and-stores of the same global is the safe default); and (b) does it
scan each function to its true end (from an independently-built function-
boundary table) rather than stopping at the first return instruction. A
census that is idiom-complete but root-incomplete produces a negative that
looks identical to a genuinely complete one — the only way to catch the
difference is to audit the root/boundary logic directly, not to keep
widening the idiom list.
