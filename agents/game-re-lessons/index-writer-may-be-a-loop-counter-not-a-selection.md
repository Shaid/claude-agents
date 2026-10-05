# "What selects this index?" may have no answer — the writer can be a sweep loop's own counter

**When it bites:** a store-site census has found where an index/handle field
gets a real value, the write is `sb/sh/sw <reg>`, and the open question has
been framed as **"what selects `<reg>`?"** — the assumption being that some
proximity test, facing check, priority sort or scoring pass picks a winner
somewhere upstream. Especially when that framing has already survived into a
docs row or a task brief, so the next session inherits it.

## What went wrong

On Valkyrie Profile (PSX, `valkyrie`), the field engine's "engaged object"
index (`ctx+0xffc`) had been traced to two store sites, both writing register
`s2`, inside one large routine. The session wrote it up as *"still open: what
selects `s2` — the actual walk-up-to-a-chest-and-press-a-button dispatch"*,
and that sentence became the TODO row and then the next session's brief.

There is no selection step. `s2` is the **loop counter** of a linear sweep
over actor slots 1..95. The routine builds the player's current attack
hitboxes, tests them against every actor's bounding box in index order, and
writes whichever index hits first. "What selects it" was a malformed
question: the answer is "position in the table", which is not a mechanism.

The real open questions were one level out, and neither was being asked:

- **What runs the sweep at all** — here, two call sites in the player's own
  per-frame function, both gated on the attack button's latched flag. That is
  the actual "press a button near a thing" trigger.
- **What happens per hit** — a jump table on the target's own kind byte,
  which is where the interesting per-object-class behaviour lives.

## The correction, generalized

A "who writes X" census answers *where X is assigned*. It does not answer
*what X is*, and in particular it cannot tell you whether the assigned value
was chosen or merely enumerated. Before framing "what selects X" as the open
item, do the cheap disambiguation: **look at what else the writing register
is used for in the same function.** If it is compared against a bound,
incremented, or used to stride a base pointer, it is an iteration variable
and there is no selection logic to find — re-aim at the loop's *entry
condition* and its *per-iteration test* instead.

Two tells that you are in this case, both visible without understanding the
routine:

- The store sits inside a backward branch whose target is above it.
- The same register appears in an `slti`/`sltu`-against-a-constant near the
  loop head (that constant is usually the real table size, free for the
  taking — on this game, `slti $v0,$s2,0x60` is the 96-slot actor table).

And a corollary about handing work on: when writing a still-open row, prefer
naming the *evidence boundary* ("this routine's callers are not traced") over
naming a presumed mechanism ("what selects X"). The first is always true and
costs a later session nothing; the second can be a wrong premise that a later
session spends its budget honouring. Related:
`negative-from-addressing-root-not-shapes.md`,
`undetermined-selection-may-be-immaterial-or-already-in-a-skipped-field.md`
(the sibling case: the question is real but the answer does not matter),
`tracker-prose-is-not-evidence.md`.

## The mirror-image trap: bound-checked/clamped/incrementing register with NO backward branch is not a repeating loop at all

The two tells above (a backward branch targeting the store, plus an
`slti`/`sltu`-against-a-constant near a loop head) don't just distinguish
"selection" from "iteration" — their *absence* distinguishes "iterates
multiple times per call" from "increments once per call, across many
calls." A register that increments by a fixed step, gets compared against a
bound, and is clamped/pinned to a sentinel once it would exceed that bound
(`v0 = min(v0+4, 0xff)`-shaped code) looks exactly like a loop trip counter
at a skim — but if there is no backward branch anywhere targeting the block
that does the incrementing, it never repeats within one call at all. It is
a plain **persistent counter that advances once per invocation** (a
"ticks elapsed, capped" value), and the surrounding if/else block that
contains it runs to completion exactly once per call, not N times.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a cutscene controller's
own body contained a register incrementing by 4 per pass, compared against
0x100, and clamped to 0xff once saturated — shaped exactly like "loop over
up to 64 slots." A search for any branch targeting the enclosing block
found none: the block executes exactly once per call to the function (which
itself re-invokes via an unconditional jump forming an OUTER per-tick loop,
called once per video frame via a confirmed VSync-wait), so the register is
really a **64-tick (~1 second) timer gating a fade-in effect and a
minimum-display-duration check**, not an inner sweep over 64 items.
Interpreting it as "process 64 slots per tick" would have produced a
completely wrong model of the function's real behavior (a per-frame batch
process instead of a simple elapsed-time gate).

**The check, symmetric to the one above:** before describing ANY
bound-compared, incrementing, or clamped register as implying repeated
execution of its enclosing block, find the actual backward branch that
would cause that repetition. No such edge → the block runs once per call;
the register's role is almost always "counts calls/ticks/frames," not
"indexes a sweep."
