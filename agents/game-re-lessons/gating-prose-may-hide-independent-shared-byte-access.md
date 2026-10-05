# "Gated on a byte that a sibling function sets" can describe two independent pollers, not a call

**When it bites:** a doc describes a poller/dispatcher function as "gated
on" or "waiting for" a flag/byte that prose attributes to "a sibling
function" or "another routine" setting it — before assuming (or building a
verify script around the assumption) that the poller calls the setter, or
that the setter's return value/side effect is what unblocks the poller.
Also worth checking whenever you're about to disassemble a producer/
consumer pair that a prior pass already named but never disassembled both
sides of together.

Retro engines routinely use no-call, no-mutex "communicate through one
byte" patterns: a setter function does nothing but idempotently write a
flag to 1 if it's currently 0, with no return value and no other side
effect; a completely separate poller, called from an unrelated place (a
per-tick driver), independently reads the exact same byte on its own
schedule and acts once it's nonzero, then clears/negates it as a one-shot
re-entry guard. Natural-language doc prose describing this ("`FUN_B`
re-reads the state, gated on a separate 'completed' byte that a sibling
function, `FUN_A`, sets to 1") is accurate about *what happens* but reads,
on a skim, as though `FUN_B` calls `FUN_A` or that `FUN_A`'s completion is
what triggers `FUN_B` — when in fact the two functions have **zero direct
call relationship** and can be invoked from completely unrelated call
graphs, at completely unrelated times, with the shared byte as the *only*
connection between them.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project): a doc section
described GODCAMP's ending-selection poller (`FUN_8003FE74`) as "gated on
a separate 'completed' byte ... that a sibling function, `FUN_8003FE4C`,
sets to 1 the first time it's read as 0" — phrasing that, read quickly,
suggests `FUN_8003FE74` invokes `FUN_8003FE4C` to check/consume the gate.
Disassembling both functions byte-exact showed they never call each other
at all: `FUN_8003FE4C` is a bare idempotent setter (poll-then-write, `jr
$ra`, no other effect, no return value used by any caller) with **six**
independent call sites — five inside unrelated per-state step-sequencer
tails, and a sixth inside a dialogue text-control-code handler with no
relationship to any of the five. `FUN_8003FE74` polls the identical byte
completely independently, from its own unrelated per-tick call sites, and
sets it to `-1` as its own tail's re-entry guard. Getting this right
mattered concretely: it meant the dialogue-code call site was a genuinely
independent SIXTH arming path (worth its own census of which real strings
carry it), not a duplicate of, or subordinate to, the five compiled
sequencers' own arming — a conclusion that "B calls A" framing would have
obscured.

**Fix:** whenever a doc's prose links two functions with gating language
("gated on", "waits for", "polls a flag that X sets", "the completion
byte X manages") rather than an explicit "calls"/"jal"/"invokes", treat
that as an open question about the call graph, not a settled one — pull
up both functions' actual disassembly and check for a direct call edge in
either direction before trusting or building on the relationship. If
there is none, enumerate the *setter's* own call sites separately from
the *poller's* own call sites: a shared byte can have many independent
writers feeding one reader (or vice versa), and a doc that's only
disassembled one of the setter's several call sites will describe the
mechanism as narrower than it really is. This generalizes past PSX/MIPS:
any polling-loop-plus-flag mechanism (a "ready" bit, a "dirty" flag, a
one-shot latch) is a candidate for this exact misreading whenever the
prose names one specific setter without having enumerated all of that
setter's callers.
