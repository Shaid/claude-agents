# A script-VM opcode that pushes a frame and returns to the dispatcher is not a call — the frame is consumed by the dispatcher's endpoint check, not by the handler

**When it bites:** porting a bytecode/event-script interpreter whose
"call"/"repeat"/"block" opcode handlers end in `rts` back to a generic
dispatcher (rather than jumping to their target), and the port models the
opcode as `push(return = next byte); pc = target`. Also bites when the
port's own unit test was written from that model, so it passes while every
real script mis-executes.

## What went wrong

FFV (SNES)'s field EventScript VM (`ceres`, `tools/ffv/overworld-gfx.ts`,
source `everything8215/ff5` `field-main.asm` `ExecEvent`/`NextEventCmd`)
has three frame-pushing opcodes — `$C7 b1`, `$CE cnt b2`, `$CF cnt b2` —
and one real call, `$CD event16`. All four handlers push a 4-word frame
`{restart ptr, end ptr, count}` onto an event stack and `rts` to the
dispatcher; **none of them writes the target address into the event
pointer**. `$C7`'s handler (`_c0a40a`) just adds 2 to the pointer and
stores `{restart: ptr+2, end: ptr+2+b1, count: 1}`; execution falls
through into the block. The frame is only ever *consulted* by the
dispatcher's next-command routine (`NextEventCmd`), which before every
fetch compares the current pointer against the top frame's END pointer:
equal → decrement the count; nonzero → jump to the restart pointer; zero →
pop, leave the pointer where it is, and **re-check the new top frame at
the same pointer** (`bra NextEventCmd`). `$FF` with a non-empty stack pops
whatever frame is on top and resumes at its end pointer — a return for a
`$CD` frame (whose "end" is the caller's return address), a break-to-end
for a block frame. So `$C7` is really "run this block once inline with the
parallel-movement flag set" (identical to `$CF` with count 1), and `$CD`
is the only opcode that changes the pointer to a new script.

A prior session modelled `$C7` as a relative *call* — jump to
`ptr+2+b1`, then "return" to `ptr+2` — which executed everything after the
block a second time, in all 988 ROM uses, and wrote a unit test asserting
exactly that order. It also popped the inner of two nested repeat frames
sharing an endpoint and executed the endpoint command directly, so the
outer loop never iterated (script 115: 20x16 = 320 particle passes
expected, 16 produced; script 1842: 4x255 = 1,020 camera moves expected,
255 produced). `$FF` inside a block terminated the whole event instead of
breaking to the block end.

## Fix / discriminators

- For each frame-pushing handler, read whether it **writes the event
  pointer** to the target before `rts`. If it only advances past its own
  operands, the target is a *boundary* the dispatcher watches for, not a
  jump destination — model one unified frame stack `{endScript, endOffset,
  restart, remaining}` and put the endpoint check at the top of the fetch
  loop, re-running it after every pop.
- Read the dispatcher's own next-command routine in full, including what
  it does after a pop (re-check vs. fetch) and what the width of the count
  decrement is (see
  `variable-width-cpu-operand-width-is-the-instruction-site-mode.md`).
- Cheap corpus oracles, no emulator needed: (a) scripts whose *only*
  control flow is the suspect opcode must trace strictly linearly, each
  offset visited exactly once (67 FFV scripts); (b) every block body in
  the ROM should contain the command class the mechanism exists for (all
  988 `$C7` blocks contain movement commands — the parallel-move flag's
  whole purpose); (c) for nested frames sharing an endpoint, hand-multiply
  the counts from the raw bytes and assert the trace count of the inner
  body.
- Sibling lessons: `jump-table-noop-means-handled-elsewhere.md` (a
  handler that appears to do nothing is handled by the dispatcher) and
  `resume-entry-citation-drops-setup-arithmetic.md` (the mechanism lives
  upstream of the label you read).
