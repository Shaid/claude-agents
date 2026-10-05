# A pooled-instance spawner's own literal handler-install address is a stronger prologue oracle than back-scanning from a call site

**When it bites:** you're disassembling a pooled-instance/vtable-style tick
handler (the `fcn.80068008`-family "allocate a slot, `sw <handlerAddr>,
0(inst)`, a generic per-frame dispatcher `jalr`s through it" convention
already documented for this engine) and had to *guess* where the handler
function itself starts — e.g. by back-scanning from a known reference point
(a caller, a census address) for something that looks like a plausible
stack-frame-setup instruction. Also fires generally: any time a
back-scanned "this looks like a prologue" heuristic is the only evidence
for a function's start address, on a fixed-width ISA where there's no
alignment/opcode-shape tell to confirm it either way. **Also fires when the
landmark you're back-scanning to is a `jr $ra`/return instruction instead
of a prologue** — at scale, resolving many previously-unnamed functions'
start addresses in one pass with no known spawner/installer to anchor
against — see the iterative convergence-resolver variant below.

## What went wrong

Tracing Valkyrie Profile (PSX)'s code-0 "First Aid" heal-over-time chain,
a function needed for its "confirm and re-fire" step was reached by
back-scanning from its own call site. The scan stopped at `0x800705dc`,
whose first instructions (`lbu`, branches, a jump) looked like a
self-contained routine — plausible, and it disassembled cleanly forward
from there with no obvious desync. It was read, interpreted (wrongly, as
"a caller-side helper"), and used to draw a conclusion about the mechanism
before the true entry point was found.

The real prologue was 14 instructions (0x38 bytes) earlier, at `0x800705a4`
(`addiu sp,sp,-80; sw s2,...; addu s2,a0,zero; ...`) — a completely
ordinary function prologue that the back-scan had walked straight past
without recognizing, because `0x800705dc`'s bytes *also* happened to look
plausible as a standalone start. On MIPS (fixed 4-byte instruction width)
there's no alignment tell to catch this the way an off-instruction-boundary
landing would on a variable-width CISC ISA — both candidate starts are
perfectly well-formed disassembly, so "does it disassemble cleanly" gives
zero discriminating signal here.

The mistake was caught, not by scanning further back or trying harder to
recognize a "more prologue-shaped" instruction, but by tracing a
*completely different* function in the same chain: the spawner
(`fcn.80070790`) that installs this handler into a freshly-allocated pooled
instance does so with a literal `lui/addiu` pair computing the exact
address, immediately followed by `sw <that address>, 0(instance)` — the
same vtable-install idiom this engine's spawners always use. That
instruction *names the real entry point directly*: `0x800705a4`, not
`0x800705dc`. Re-scoping the disassembly to start there changed the whole
interpretation of the function from "a caster-side helper" to "a
per-instance tick handler taking the instance as `a0`" — a materially
different (and correct) reading.

## Fix

When a function belongs to a pooled-instance/vtable-handler engine family
(this convention recurs across this account's PSX corpora — VP1, Parasite
Eve's actor packages, others), don't rely on a manual back-scan or a
"looks like a prologue" heuristic to pin its start address, even when the
resulting disassembly looks clean. Instead, find the spawner/installer that
assigns this function as a handler — it will contain a literal
`lui`/`addiu`-built (or platform-equivalent immediate-load) address
immediately preceding the `sw`/store into the instance's handler slot. That
literal is ground truth for the function's real entry point, cheaper than
re-scanning and immune to the "two different addresses both disassemble
plausibly" trap a fixed-width ISA gives you no other way to break. Treat
any back-scanned "prologue" as a hypothesis until either (a) a literal
install/reference elsewhere confirms the exact address, or (b) the function
has a confirmed unconditional-transfer/return right before it with nothing
in between.

## Variant: the back-scan finds a *real* stack prologue and is still wrong, because the compiler hoisted a load above it

The case above is a back-scan stopping at something that merely *looked*
like a routine start. The same file covers the harder variant, where the
back-scan stops at a genuine, textbook `addiu $sp,$sp,-N` frame setup — the
strongest prologue signal the ISA offers — and the function still begins
earlier. Compilers routinely hoist a cheap, frame-independent setup
instruction (a global/flag load, an argument move) *above* the stack
adjust, so on MIPS/RISC generally **the stack prologue is not guaranteed to
be the function's first instruction**, and a scan that keys on it lands a
few instructions late with nothing off about the resulting disassembly.

Confirmed on Valkyrie Profile (PSX) again, a different chain: a battle
transition task at `0x8006474c` was traced back to a caller located by
back-scanning to the nearest preceding `addiu $sp,$sp,-0x70`, giving
`0x8005ee04`. The real entry was `0x8005edfc`, **eight bytes earlier** — the
compiler had emitted `lui $v0,0x8008` / `lw $v0,-0xda0($v0)` (a field-flags
gate load) ahead of the stack adjust.

**The tell is worth generalizing past prologues: a corpus-wide census for
an address that returns *zero* hits is evidence the address is wrong before
it is evidence of unreachability.** Here, a materialisation census for
`0x8005ee04` found 0 sites and the engine's task-function-pointer table
didn't list it either — two independent negatives that very nearly got
written up as "this handler is unreachable / must be reached some other
way," a conclusion that would have been both wrong and expensive. Real
engine code is referenced *somewhere*; a total absence points at your
address, not at the code. The same reasoning applies to a wrong base, a
wrong segment, or an off-by-a-few entry, not just a hoisted prologue.

**Second fix, nearly free:** once an entry address is corrected, grep the
project's own `docs/` for the new value before analysing anything. The
corrected `0x8005edfc` was *already documented* in this same project's
`dungeon-field-mechanics.md` as the container/chest task installed by scene
opcode 204 — which explained the entire structure instantly and saved a
from-scratch trace. A candidate entry address is a free cross-reference key
into work earlier sessions already did; the wrong one by definition matches
nothing, which is itself part of why the 0-hit result should have prompted
doubt sooner.

**The grep is mandatory even when you get the address right the first
time, not only after correcting a wrong guess.** A later round on this same
project (Valkyrie Profile PSX) found `0x8005edfc`'s real prologue via
exactly the correct method this file recommends — a genuine backward `jr $ra`
walk from an arbitrary point in its already-known dispatch tail, landing
cleanly on a real `addiu $sp,$sp,-N` frame setup with a `lui`/`lw` gate load
hoisted above it (the same hoisting shape described above) — and then wrote
up "`0x8005edfc`, never before cited by address" without ever grepping for
it. It was wrong: this is the *exact* address and the *exact*
`0x8006fd90`-`0x8006fda8` install-site range this very lesson file already
names above, from `dungeon-field-mechanics.md` § 20.5. The round's own
tracing of what the function's *body* does once installed was still
genuinely new and valuable (§ 20.5 only documents the installing code) — but
the false "first discovery" framing had to be corrected in place after the
fact, once a routine post-round lesson-harvest re-surfaced this very file.
**Sharpened fix:** treat "grep the docs for this address" as a mandatory
step every time you finish deriving ANY function's real entry point and are
about to write it up — regardless of whether you arrived there by fixing a
wrong backscan or by a clean, correct derivation from the start. Getting the
address right is not evidence you're the first to have it.

## Variant: bucketing many independently-found addresses by "nearest preceding prologue" can span past a function's real end into the next function entirely

The variant above is about finding ONE function's own start. A related but
distinct mistake shows up when grouping MANY separately-located addresses
(e.g. every site that tests one flag bit, found by an exhaustive corpus-wide
census) by "which function contains this address" — a common cheap
heuristic walks backward from each address to the nearest instruction that
looks like a stack-frame prologue and buckets by that. This assumes each
function has exactly one such landmark and that the heuristic correctly
bounds it on the far end too — but a large function with only one prologue
near its own start, and no internal secondary `addiu $sp,$sp,-N` anywhere in
its body, will happily "contain" every address up through ones that are
actually inside the NEXT function, because the heuristic never checks for
that function's own real terminating `jr $ra` in between.

Confirmed on Valkyrie Profile (PSX): one round of a long-running flag-bit
investigation bucketed 10 flag-test sites under "nearest preceding prologue"
and described them as one function (a plausible-sounding but wrong
"party/formation-member propagation" mechanic). A later round walked FORWARD
from that same prologue to the function's real end via its first actual
`jr $ra` — landing exactly on an address a completely different, already-
published citation in the project's own docs had independently given as
that function's real length. Only 6 of the original 10 sites fell inside
that verified span; the other 4 were in the function starting immediately
after — itself a third, already independently-documented function elsewhere
in the project. The prologue-bucketing heuristic had silently merged sites
from two adjacent, unrelated functions into one bucket, and the resulting
wrong mechanic name survived a full round of published prose before a
second pass caught it.

**Fix:** before trusting a group of addresses attributed to one function by
"nearest preceding prologue-shaped instruction," forward-walk from that
prologue to the function's own real `jr $ra` (or cross-check an independent
length citation already in the project's docs) and verify every address in
the group actually falls inside that span. "No visible internal prologue for
a long stretch" is not evidence a whole address range belongs to one
function — it's only evidence the heuristic has nothing to stop it early.

## Variant: the nearest preceding `jr $ra` can be the SAME function's own early return, not the previous function's true end

The variants above are about back-scanning to a *prologue*-shaped landmark.
A related but distinct failure shows up when there's no known
spawner/installer to anchor against at all, and the fallback is
back-scanning to the nearest preceding *return* instruction (`jr $ra` on
MIPS, `rts` on 68k) and treating everything after it as "the function."
That landmark can be a perfectly genuine, reached `jr $ra` — a real
function boundary — and still be the WRONG one: dispatcher/state-machine
bodies routinely have several `if (cond) return;`-shaped early exits, each
a well-formed `jr $ra` a naive backscan will happily stop at. If the one it
stops at belongs to the SAME function that contains your target address
(an early return partway through, not the previous function's true end),
the resulting "start" understates the real function boundary and
misattributes every site in between.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): round 25 of a long-running
census needed to pin the containing function for 19 newly-attributed sites
across 11 functions that had never been named before, at scale, with no
spawner/installer citation to anchor most of them. The fix was an
**iterative backward/forward convergence resolver**: from the nearest
preceding `jr $ra`, walk FORWARD from its own delay slot to find that
candidate's own real end (its own next `jr $ra` whose forward walk doesn't
loop back over already-visited code). If the target site falls OUTSIDE the
resulting `[start, end)` range, the assumption was wrong — that `jr $ra`
was really a mid-function early return of the function containing the
site, not a genuine prior-function boundary. Back up to the next-earlier
`jr $ra` and repeat the same forward-walk check. This converges on the
site's true containing function's real start regardless of how many early
returns precede it, and is mechanically self-verifying (the target site
lands inside a self-consistent, forward-walk-confirmed range) rather than
a one-shot guess. Independently re-run as a second implementation of the
same algorithm, it reproduced the identical owning-function start for all
19 sites with 0 deviations from a hand-built lookup table, and every one
of the 11 newly-bounded functions' `jr $ra` boundaries were separately
structurally verified byte-exact.

**Fix, generalized:** when no literal-install site or independent length
citation is available to anchor a function's start (this file's primary
fix), and the fallback is back-scanning to a `jr $ra`, never trust the
first one found — forward-walk from it to verify it's a self-consistent
boundary for the target site, and iterate backward through however many
false "starts" (real but early-exit `jr $ra`s of the target's own
function) it takes to converge. This is the return-instruction-landmark
counterpart to the prologue-bucketing variant above; both are instances of
"a backscanned landmark needs a forward-walk to confirm it actually bounds
what you think it bounds."

## Variant: the literal-construction census's hit can sit inside an already-documented, much larger SIBLING function, not a dedicated spawner

This file's primary fix assumes the literal `lui`/`addiu`-built handler
address sits inside a small, dedicated spawner function. It doesn't have
to — the same census can land inside a large function you already have
fully documented for an unrelated reason, and the temptation is to assume
a still-undiscovered spawner must exist somewhere else instead of checking
the hit's own containing bounds.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 26 of the
`vp1psx-scene-script-opcodes` campaign: a task-pool function `0x8006623c`
had 0 direct `jal` callers, and three prior rounds re-confirming its
existence had never located an installer for it. Running this file's own
literal `lui`/`addiu`-construction census for the exact 32-bit target found
exactly 2 hits — and both fell inside the bounded body of `0x8005edfc`, a
1747-instruction task the project had already extensively traced, under a
different name, a dozen rounds earlier (the "container task" step
function). The installer was never missing; it was sitting inside a
function everyone had already read, just never re-scanned for this
specific literal.

**Fix:** once a literal-construction census returns a hit address, first
check whether it falls inside the `[start, end)` range of a function you
already have a confirmed `jr $ra`-walk boundary for (this file's own
technique, applied to every already-named function in the project) —
before assuming the hit names a still-to-be-found, dedicated spawner. Run
this census as the *first* move (not a fallback tried only after a
`jal`-target census returns zero — which this file's core fix already
treats as the default) whenever a task-pool/handler-table function shows 0
direct callers, and always resolve the hit's own containing function before
writing "installer not found" or "must be reached some other way."
