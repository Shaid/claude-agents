# A function's own `jr $ra`/`RTS`/`RET` being unreachable can be correct, not a bug — check whether a callee is a confirmed overlay-swap/context-reset primitive

**When it bites:** a linear disassembly AND a branch-following CFG walk both
agree that a function's own return instruction is never reached from its
entry point — every path loops back on itself or falls into an unconditional
jump — and the temptation is to call this a disassembly error, an
unidentified computed jump, a fiber/coroutine scheduler, or "needs live
capture to see how it really exits." Before reaching for any of those, check
whether one of the function's own callees is a mechanism *this same project*
has already confirmed to overwrite the running code region and jump to a
fresh entry point (an overlay loader, a "reset $sp and reboot the
subsystem" primitive, a bank-switch-and-jump routine). If so, the missing
return is not a bug to explain — the function terminates by replacing
itself, and there was never a `jr $ra`/`RTS` to reach in the first place.

## What went wrong (and how it resolved)

On Valkyrie Profile (PSX, `valkyrie`), a room's dialogue/portrait-cutscene
controller (a `TASK`-table native routine, ~470 MIPS instructions) linearly
disassembled to an unconditional `j` back to its own mid-body loop entry
immediately before its own epilogue — making the epilogue look like dead
code. To rule out a missed backward branch a linear read could hide, the
project's own branch-following CFG walker (already built for exactly this
class of question) was re-run over the function: it independently confirmed
0 reachable paths to the epilogue, and confirmed the function contains no
other `jr`/`jalr` anywhere that could reach it dynamically either. That is
airtight evidence the function's own instruction stream never returns.

The resolution took one more step, not an escalation: one of the function's
own literal call targets (`fcn.800105b0`, called with a specific argument
value or calling convention already established elsewhere) matched — byte
for byte, argument for argument — a mechanism the SAME project's own docs
had *already* fully traced and confirmed months earlier from a completely
unrelated call site: an "overlay loader" that decompresses a buffer, then
issues a hardcoded jump to a fixed entry address, effectively replacing
the entire currently-running code region (including the calling function's
own body) with a freshly-loaded one. Once that callee's real effect is
known, the "unreachable epilogue" stops being a mystery: the function
doesn't return in the ordinary sense, it terminates its own lifetime by
self-overwriting. No emulator, no live capture, and no further disassembly
depth was needed — just recognizing the call target against prior art
already sitting in the project's own documents (see
`doc-self-cross-reference-before-fresh-disassembly.md` for the general
"check your own docs first" habit that surfaces this kind of match).

## The generalizable pattern

This class of "function never returns" is common in any engine with one or
more of:

- **Dynamically-loaded overlays sharing one fixed runtime base** (PSX field/
  battle/menu overlay swaps, Amiga's disk-resident overlay chains, any
  console architecture that streams code over a fixed memory window) — a
  "load and run overlay N" primitive routinely resets the stack pointer and
  jumps to a hardcoded entry address, by design, as its *normal* behavior,
  not an edge case.
- **Bank-switched ROM/RAM code** on 8/16-bit hardware, where a "switch bank
  and jump" routine has no reason to preserve a return address that would be
  meaningless after the switch.
- **State-machine "scene transition" or "mode change" dispatchers** that
  intentionally never unwind the calling function's stack frame because the
  whole point is to abandon the current mode's context.

**The check, cheaply, before assuming anything exotic:**

1. Confirm the return is genuinely unreachable with a CFG walk, not just a
   linear read (a linear read can't rule out a backward branch it hasn't
   seen yet, and a CFG walk can't be fooled by an unconditional jump that
   merely *looks* like an exit).
2. List every literal call target inside the function (not just the ones
   near the "dead" epilogue) and check each one against the project's own
   already-confirmed mechanisms first — specifically anything previously
   documented as an overlay/bank/mode loader, a stack-reset primitive, or
   "resets `$sp`"/"jumps to a fixed entry" in its own write-up.
3. Only if no such match exists should you widen to disassembling the
   callee bodies themselves for stack/`$ra` manipulation, and only after
   that should "needs live capture" or an escalation brief be considered —
   a self-overwriting overlay swap is a *far* more common explanation than
   a genuinely novel coroutine/fiber mechanism, and it costs nothing beyond
   a grep of your own docs to check first.

This is the semantic-payoff half of
`doc-self-cross-reference-before-fresh-disassembly.md`'s cross-referencing
habit: that lesson tells you *to* grep your own docs before disassembling
further; this one names the specific *kind* of answer you're likely to find
when the open question is "why doesn't this function return."
