# To sample a fully-computed register mid-function with a scoped CPU interpreter, patch one instruction to an immediate return rather than running to the function's real end or extending the interpreter

**When it bites:** verifying a sub-expression or accumulator that's fully
computed partway through a larger function (no natural `jr $ra`/`ret`
nearby — control keeps going into unrelated code, a loop, or a dispatch
this pass doesn't need or want to model) via a small scoped CPU interpreter
(the `mips-interp.ts` pattern: unsupported opcodes/targets throw, so a
clean run is itself evidence). Running to the function's real end pulls in
everything downstream (extra memory/register setup, calls this pass isn't
trying to verify); the interpreter's own `run()` only stops on a `jr $ra`
matching its sentinel return address.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 212: verifying the
exact formula a caller uses to build a "render mode" flags word required
sampling one fully-computed accumulator register right before the
function's very next instruction (a `bnez` on that same register)
dispatches into a much larger, unrelated code path. There is no return
instruction anywhere near that point. Rather than extend the interpreter's
public API with a "run N steps" or "run until PC == X" mode, the fix was
to take a writable copy of the loaded overlay bytes (already the pattern —
`mem.addRegion(base, overlay.slice())`) and overwrite the single
instruction word at the sample point with `jr $ra`'s encoding
(`0x03e00008`), leaving its own delay slot as whatever `nop`/harmless
instruction real bytes already had there. `run()` already presets `$ra` to
its sentinel, so execution reaches the patch and returns cleanly, with
every byte before the patch point being real, unmodified code that
actually executed.

**Fix / general technique:** when a scoped interpreter's `run()` contract
is "stop at return," and the thing you need to observe has no return
nearby, patch a single instruction in your OWN in-memory copy (never the
on-disk file) to a `jr $ra` (or your ISA's return) at the exact point after
the value is finalized — verify the memory copy is writable (`.slice()` of
the source bytes, not a shared reference) and that the patched
instruction's own delay slot (if the ISA has one) is something harmless.
This keeps the interpreter's API minimal and untouched while still letting
you verify an arbitrarily deep mid-function computation against real
bytes, which is strictly stronger evidence than hand-tracing the same
span by eye.
