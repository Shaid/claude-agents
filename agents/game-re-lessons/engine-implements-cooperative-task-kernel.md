# A "boot/init routine with zero direct ROM callers" can be a real OS-like task scheduler, not just an indirect jump table

**When it bites:** an exhaustive branch/call scan (every encoding) for a confirmed-reachable routine finds zero callers, and you are about to widen the encoding search or assume a state-indexed `jmp (An)` table. Also: any target with per-instance records holding a function-pointer field and a generic per-tick dispatcher (68000, MIPS, any ISA).

If the routine is reached by a function pointer read from RAM, its address never appears as a branch operand — the zero is *correct*, and more branch-scanning cannot help (`negative-from-addressing-root-not-shapes.md`). Two shapes produce it: a cooperative task kernel (register-task syscall + task table + dispatcher), or — simpler and more common — a task record whose own handler overwrites its `fn` field to hand off to a sibling handler on the next tick.

**Check / fix:**
1. **Scan for the routine's address as data**: a literal 32/16-bit scan, and on MIPS a `lui`/`addiu` construction census (68k: `movea.l #imm,An`/`lea addr.l,An`). Hits preceded by an immediate-load opcode and followed by a store into a record field, or a call to a fixed trampoline, mean the address is *registered*, not called.
2. **If the write sites share an idiom** (`movea.l #fn,a0 / move.w #slot,d0 / jsr $TRAMPOLINE`), census every call to that trampoline — it yields the whole task registry, not just your target.
3. **Find the task array via `LEA <base>,An`** (base guessed from the trampoline handler) rather than tracing registers forward from the indirect call; it finds the dispatcher and every other walker of the array.
4. **Kernel tells:** `TRAP` used as a general syscall convention; a fixed-stride RAM array with a pointer-sized field; a per-slot stack-pointer table (≈16 RAM addresses spaced by a round size like `0x80`) near the trampolines.
5. **Self-repointing tell:** a function with zero `jal` callers immediately after another's `jr $ra`, whose address the preceding function builds and stores into `task.fn` (or passes as a `findTask` key).

**Canonical example:** Knights of the Round (CPS1, `kolbold`): init routine `$f4a` had zero branch callers in the 1 MB ROM. A literal scan found `0x00000f4a` twice, both as `movea.l`/`lea` immediates before `jsr $e72.w` — a `TRAP`-vectored "register task" syscall into a 16-slot TCB array (status, function pointer, params). Censusing calls to `$e72` found 77 registrations; the round-robin dispatcher does `movea.l TCB+4(a0),a1 / jmp (a1)`; a matching `TRAP` terminates one-shot tasks. A `LEA <array>` scan also found the VBLANK per-slot timer decrement.

**Variant:** Valkyrie Profile PSX (`valkyrie`): no kernel. Generic dispatcher calls `task.fn(task)` each tick; `FUN_8006a500` (prop restore "wait" phase, returns at `0x8006abec`) builds `0x8006abf4` with `lui`/`addiu` at `0x8006a8ac`/`0x8006a9e4` and stores it into its own `fn` (`sw $v1,0x0($s2)`). `0x8006abf4` (the "release" phase) has 0 `jal` callers; a third site uses it as a `findTask()` key. Same pattern drives `0x80065b6c` (hit-reaction task). See `spawner-install-literal-outranks-backscan-prologue.md` for the adjacent boundary trap.

**History:** 3 recorded instances (kolbold KotR, valkyrie ×2) — full log in `_archive/engine-implements-cooperative-task-kernel.md`.
