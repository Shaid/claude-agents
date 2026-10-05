# The bounded interpreter + hook table — a third option between hand-porting and full emulation

**When to reach for this:** a game's per-unit/per-object behaviour is not data
at all but *hundreds of small compiled code blobs* (enemy AI modules, spell
scripts, per-actor state machines) that call back into the engine. Hand-porting
each blob is hopeless (there are hundreds, and they're compiler output). A full
hardware emulator is the wrong shape too — you don't want the game's renderer,
audio or scheduler, you want its *logic* running against **your** engine's
state.

The middle option: interpret the CPU faithfully, and hook only the calls that
leave the blob. It works whenever a census can show the call surface is
bounded.

Worked example: Valkyrie Profile (PSX, `valkyrie`), 655 behaviour modules
(551 enemy + 104 party), `src/engine/interpreter/`, docs
`docs/valkyrieprofile/psx/battle-engine-spec.md` § 11.

## Scope it with a census first, then encode the census as assertions

Before writing a decoder, run a control-flow-verified census over the whole
blob corpus and answer: which instruction classes actually occur, which
addresses are called, is there self-modifying code, is there hardware I/O.
(Do this by real control flow, not a linear scan —
`fixed-width-isa-blind-decode-census-inflates-exotic-opcodes.md`.)

The payoff is not just knowing what to implement. **Every "this never occurs"
result becomes an executable assertion.** VP1's census found 0 reachable
`syscall`, 0 COP1, 0 branch-likely, 0 self-modifying writes and 0 hardware
I/O. So the interpreter *raises* on each of those rather than implementing a
guess or a no-op. If one ever fires, the interpreter is off the rails and says
so at the exact instruction, instead of silently producing a plausible wrong
run.

Apply the same rule to memory: declare the regions the census says exist
(blob image, the object struct, the global context, stack, scratchpad) and
**fault on anything outside them** rather than reading zero. Most of the bugs
this catches are your own address arithmetic, and a fault names the address.

## Hook the engine calls — and never stub an *unrecognised* one

Build a table keyed by absolute call target. Three honest categories, and the
distinction matters more than the count:

- **native** — the docs pin both the ABI *and* the effect; implement it
  against your real engine primitives so the blob drives actual game state.
- **partial** — one confirmed observable is implemented, the rest isn't. Say
  which, in the code, with the doc section.
- **stub** — you recognise the call but genuinely do not know what it does.
  A stub is *not* a claim that the call does nothing. Log it, and let the
  caller supply the return value, because some stubs gate real control flow
  (VP1's animation drivers select which phase a handler runs).

An **unrecognised** target must raise, not fall back to a generic stub. That
single choice is what makes "this blob ran to completion" a *proof* that your
hook table covers its entire call surface — the most useful result the whole
exercise produces, and you get it for free on every blob you run.

Two practical notes: hooks receive the caller's frame, so read stack arguments
at the ABI's outgoing-argument area (`sp+0x10` for MIPS o32) — and if the ISA
has delay slots, invoke the hook *after* the delay-slot instruction has
executed, or you'll read arguments the delay slot was about to set.

## Execution is an oracle that corrects the static census

This is the part that's easy to underestimate. Running real blobs found things
a careful static pass had got wrong:

- Two entry-point *shapes* the census had filed as "a prologue variant our
  heuristic misses" turned out to be entirely different mechanisms (a
  96-entry state jump table; a degenerate one-action inline dispatch). The
  static pass's proposed fix — "widen the search window" — would never have
  worked.
- An unknown engine function documented only as "RNG utility" was pinned to
  `rand() % a0` by how a caller *tested* its result (see
  `nearest-preceding-immediate-is-not-dataflow.md` for why the caller's test
  is the evidence and an argument histogram alone isn't).

So budget for the census to be wrong in places, and treat the first real
execution as a verification pass on it, not just on your decoder.

## Ground the tests in effects documented independently of the interpreter

Pick blobs whose behaviour some *other* pass already nailed down, so the test
can't be circular. VP1's three: a move-name banner whose battle-text id
(1316 = "Hydrophobia") a prior pass had recovered byte-exactly and
corroborated against a published bestiary; a status-inflict call with a
literal mask reaching the engine's own already-tested status pipeline; and an
animation trigger writing a confirmed struct field. Each asserts the *engine's*
state changed, not that the interpreter took some path.

Don't wire the interpreter into the live game loop until those pass. A
working, tested, not-yet-live interpreter is a perfectly good delivery — and a
much better one than a wired-in interpreter you can't demonstrate is correct.
