# A "computed at run time" operand in a compiled-script VM is usually a function parameter, not a table read — resolve it interprocedurally

**When it bites:** a scene/event/script VM has two operand encodings — an
immediate ("literal form") and a stack/variable form where the value is
pushed by the preceding instructions — and a large fraction of the corpus
uses the stack form. The natural reading is "these are data-driven: the
value comes from a table, and finding that table is the job." Also bites
when a per-site census inflates a count enormously, so a mechanism looks
far more widespread than it is.

Confirmed on Valkyrie Profile (PSX). Of 1,756 battle-launcher sites
(opcode 134), 1,147 had a non-literal argument, documented as "computed at
run time." Bucketing **all** of them by the mnemonics of the preceding
three instructions produced only **three** distinct shapes, and every one
ended in `LOAD32.l 0x0000` — local slot 0, i.e. the function's first
parameter. Scene scripts in this engine are compiled C-like code: opcode 24
`ENTER` followed by a run of `STORE32.l` is a prologue popping arguments,
and `CALL` targets a word index. Once that was recognised, a ~60-line
interprocedural resolver (fold constants → follow an intra-function store →
recognise a parameter → jump to each caller's corresponding push,
depth-limited and cycle-guarded) resolved the argument at **every** site,
and never found a table anywhere. The 1,147 "data-driven" sites were calls
into one shared helper, `startBattle(encounterSlot, sysset0, sysset1,
counterSlot)`, whose callers push compile-time literals.

**The load-bearing gotcha: the prologue pops arguments in REVERSE push
order.** Parameter *k* is supplied by the push `(argc − k)` instructions
before the `CALL`, not the *k*-th one after it. Reading it the other way
round does not fail loudly — it resolves each site to a plausible
*sibling* argument (here `2258`, a valid-looking id, instead of the correct
`1352`), so every sanity check still passes and the whole census comes out
quietly wrong. Pin the direction against one site whose answer you already
know before running the resolver over a corpus.

**Second trap in the same census: a linked-library helper inflates site
counts.** The helper above was statically linked into ~1,118 separate
scripts, appearing byte-identical at the same word index in each, so a
naive per-site scan reported ~1,118 independent launchers where there is
exactly one routine. Before treating a large site count as a measure of how
widespread a mechanism is, check whether the surrounding words are
identical across scripts — a duplicated library body is one mechanism, and
collapsing it usually shrinks the problem from "thousands of unexplained
sites" to "one function, find its callers."

**Fix:** when a script VM's operands are frequently stack-form, first
determine whether the VM's compiled-function convention is recognisable
(an `ENTER`-like prologue, a `CALL` opcode, local-slot loads). If so, treat
a runtime-valued operand as an interprocedural dataflow question, not a
data-format question, and write the small resolver — it is cheap, it
terminates, and "no table exists" is a legitimate, checkable answer that a
table hunt can never produce.

**Even a SINGLE stack-form occurrence deserves this treatment, not just a
large inflated count — and even in the same project/engine that already
taught this lesson once.** A follow-up pass on this exact VM found the
one and only stack-form occurrence of a different opcode (`EVENT_CG`) and
read its two preceding operand-stack loads as "runtime variable reads,"
concluding the argument was "computed at runtime, not statically
resolvable" and filing the resource ids it might have shown as a hardened
negative. They were not generic runtime reads: they were `LOAD32.l`s of
local slots 0/1/2 immediately after an `ENTER` a few words earlier — i.e.
exactly this engine's own already-documented parameter-prologue shape,
just missed because the check was applied to whether *this one occurrence*
looked resolvable, not to whether it sat inside a script-local function
whose *own* call sites might all push literals. Once recognised as a
3-argument local function, all 11 of its real call sites turned out to
push a literal resource id apiece — a literal census the ambiguous single
occurrence had been silently standing in for. **Generalized fix:** a lone
stack-form/"runtime" operand inside a script VM with a known
`ENTER`/parameter convention should always be checked for "is this read
actually a local-slot load inside a callee, whose real literal lives at
the callee's OWN call sites" before being accepted as unresolvable — don't
let a large inflated site count (the usual trigger for this lesson) be the
only thing that prompts the check; a single occurrence is exactly as
capable of hiding a callee full of literal-pushing callers.
