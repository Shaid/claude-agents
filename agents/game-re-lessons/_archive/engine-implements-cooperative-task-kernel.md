# A "boot/init routine with zero direct ROM callers" can be a real OS-like task scheduler, not just an indirect jump table

**When it bites:** an exhaustive `bsr`/`bra`/`jsr`/`jmp` (all encodings —
absolute-long, absolute-short, PC-relative) scan for a confirmed, fully-traced
routine's address finds **zero** hits anywhere in the ROM, and the natural
next hypothesis is "a game-mode/stage-select dispatch table indexed by a
small state variable feeds a `jmp (An)`" — on 68000-class (or similar)
arcade/console hardware from the mid-to-late-1980s onward, a `TRAP`/software-
interrupt-vectored **cooperative multitasking kernel** is a real, concrete
alternative worth checking before assuming a flat jump table. **The same
"zero direct callers, confirmed reachable anyway" symptom also has a much
simpler, ISA-agnostic cause with no kernel or syscall convention involved
at all** — see the MIPS variant below: a single task/state-machine record
overwriting its OWN dispatch-pointer field to hand off to a sibling
handler, picked up by an ordinary generic `task.fn(task)` per-tick
dispatcher. Suspect this first on any target (68000, MIPS, or otherwise)
that has a per-instance record with a function-pointer field and a generic
dispatcher that calls through it every tick/frame.

## What this looks like when it's real

Confirmed on Knights of the Round (CPS1, `kolbold` project): the fully-traced
game-(re)initialization routine at maincpu `$f4a` had exactly zero direct
branch-instruction callers anywhere in the 1MB program ROM (confirmed by a
prior session's exhaustive scan). The actual mechanism was a genuine 16-slot
task/process kernel built directly into the 68000 program:

- A runtime **Task Control Block (TCB) array** in work RAM (16 slots, fixed
  stride, a status/state field + a function-pointer field + a couple of
  small parameter fields per slot).
- A `TRAP #N`-vectored **"register task" syscall**, called via a fixed
  trampoline address (`jsr $e72.w` in this game) throughout the ROM — pass a
  function pointer and a slot number, it writes the pointer into that slot's
  TCB and marks the slot active. A byte-pattern scan for every call site of
  this ONE fixed trampoline address found 77 real registrations across the
  whole ROM — a much richer and more useful census than hunting for `$f4a`
  itself, because it's the SAME mechanism every persistent subsystem and
  one-shot init task uses.
- A **round-robin dispatcher loop** that scans all N slots looking for one
  whose state says "ready".
- The actual **computed jump**: `movea.l TCB+4(a0),a1 / jmp (a1)` — the
  function pointer is read fresh from RAM on every invocation, so it can
  never appear as a literal operand in any branch instruction in ROM. This is
  why the exhaustive direct-branch scan was *correct* to find nothing — the
  scan technique itself was structurally incapable of finding this class of
  target (see `negative-from-addressing-root-not-shapes.md` for the general
  form of this trap).
- A matching `TRAP #N` "terminate current task" syscall that frees a slot —
  confirming one-shot ("run once, then die") vs. persistent tasks.

## The technique that cracked it

The exhaustive branch scan had already correctly returned zero — more
branch-scanning would not help, because the target genuinely isn't a branch
operand anywhere. The decisive move was switching from "search for what
CALLS the routine" to "search for what LOADS the array/mechanism the routine
is registered into":

1. A literal 32-bit scan for the target routine's own address (`0x00000f4a`)
   found it appearing exactly twice — both times immediately preceded by a
   `movea.l`/`lea` opcode (an immediate-load operand), never as a branch
   target. This ruled out "flat table of absolute jump addresses" and
   pointed straight at "this address gets written somewhere as DATA, via a
   recognizable small instruction idiom" (a registration call).
2. Once that idiom (`movea.l #fn,a0 / move.w #slot,d0 / jsr $TRAMPOLINE`) was
   recognized at both sites, a scan for every call to that SAME fixed
   trampoline address found all 77 registrations project-wide in one pass —
   turning a single-target mystery into a full census of the game's task
   registry.
3. Separately, a scan for `LEA <task-array-base>,An` (guessing the array's
   base displacement from the trampoline's own already-partly-disassembled
   handler body) found the dispatcher loop and every other place in the ROM
   that walks the same array — including the VBLANK handler's own per-slot
   timer-decrement routine, closing an unrelated small loose end for free.

## Generalization

When a routine (or a suspiciously similar "no direct callers" result recurs
for a *second* target) is confirmed real and reachable, but a branch-scan
comes back empty:

- Don't just widen the branch-encoding search (opcode coverage was already
  complete). Instead ask: **is this routine's address ever written as DATA
  somewhere** (a literal 32-bit/16-bit scan for its own address, independent
  of instruction-decode assumptions)? If yes, and the write sites share a
  small, repeating instruction idiom, that idiom is very likely a
  "register this as a callback/task" syscall convention — find every OTHER
  call to the same syscall trampoline, not just the one you started from.
- If you can identify the array/structure the callback gets stored into,
  search for the `LEA <base>,An` that loads its address, rather than trying
  to trace every register write forward from the indirect call site (which
  is what `negative-from-addressing-root-not-shapes.md`'s general fix
  recommends, but is much more expensive when the "register" in question is
  reloaded from a data structure inside a shared, reusable dispatcher rather
  than set up freshly at one call site).
- This pattern — a real cooperative kernel, not just "a jump table" —
  is worth actively suspecting on any arcade/console 68000 (or similar)
  target once you see: (a) `TRAP`/software-interrupt instructions used as a
  general-purpose syscall convention (not just for debugger breakpoints),
  (b) a fixed-stride array in low/scratch RAM with a function-pointer-sized
  field, and (c) a per-slot private stack-pointer table (a strong tell — a
  16-entry table of otherwise-inexplicable RAM addresses spaced by a
  suspiciously round stack size, e.g. 0x80 bytes, right next to the
  syscall trampolines, is almost certainly a per-task USP table).

## Variant: no kernel needed at all — a single task's own body re-points its OWN dispatch-pointer field (confirmed on MIPS, not just 68000)

Confirmed on Valkyrie Profile (PSX, MIPS R3000A, `valkyrie` project),
across two independent instances (round 10/22's `0x80065b6c`, and round 25's
`0x8006abf4`): a task-record convention where a generic per-tick dispatcher
calls `task.fn(task)` every frame, and a task's own handler body can
overwrite `task.fn` mid-execution to transition to a *different* handler
on the *next* tick — no separate "register task" syscall, no fixed
trampoline, no shared kernel data structure at all. This is a strictly
simpler mechanism than the CPS1 TCB-kernel case above, but produces the
identical symptom: the second-phase handler function has **zero** direct
`jal`/branch-instruction callers anywhere in the binary, because it is
only ever reached by the first-phase handler quietly rewriting a data
field, never by a call instruction.

Concretely: `FUN_8006a500` (the "wait" phase of a liftable/throwable-prop
restore task) returns at a real `jr $ra` (`0x8006abec`), immediately
followed in memory by a structurally unrelated, frameless function
`0x8006abf4` (the "release" phase) that a naive linear read could mistake
for more of the same function — see
`spawner-install-literal-outranks-backscan-prologue.md` for that specific
boundary trap. `0x8006abf4` has 0 direct `jal` callers. It is reached
because `FUN_8006a500`'s own body contains two internal sites
(`0x8006a8ac`/`0x8006a9e4`) that each build the literal `0x8006abf4` via
`lui`/`addiu` and store it straight into the task's own `fn` field
(`sw $v1,0x0($s2)`) — picked up by the generic dispatcher next tick. A
third site elsewhere calls the project's own `findTask()` primitive with
`fn=0x8006abf4` as the search key, checking whether a release-phase
instance is already pending before doing something else. The identical
self-mutation pattern, found independently and earlier, drives the same
project's hit-reaction/flash task family's own `0x80065b6c`.

**Generalization:** don't read a "zero direct callers" result for a
confirmed-reachable function as a signal to widen the call-instruction
census (more encodings, more addressing modes) — check first whether the
function's own address is ever *constructed as a literal* (the
`lui`/`addiu` pair on MIPS; `movea.l #imm,An`/`lea addr.l,An` on 68k; the
platform equivalent elsewhere) immediately before a *store* into a
struct/record field, independent of what later reads that field. This is
the exact same literal-construction census the 68000/TCB-kernel case above
used to find syscall-registration sites — it works identically, and just
as cheaply, when there is no kernel or syscall convention at all, only a
task record overwriting its own next-handler pointer. It generalizes past
68000 arcade hardware to any ISA and any task/state-machine engine with a
callable function-pointer field, which is a far more common shape than a
full cooperative kernel.
