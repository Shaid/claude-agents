# A MIPS branch's delay-slot instruction executes on BOTH the taken and not-taken path — reading it as "belongs to the not-taken branch" silently mis-derives a formula

**When it bites:** reading MIPS (PS1, PS2, PSP, N64) where a branch or `jr`/`j` is followed by an instruction writing a register used afterwards — deriving a formula, a loop's accept/reject sense, or a return value (`$v0` set in a loop-exit delay slot). Also: citing an instruction address, placing a function boundary after `jr $ra`, or verify scripts that count words from an anchor.

The instruction after a branch is issued before the branch resolves, so it runs on **every** path. Top-to-bottom reading treats it as the first line of the fall-through block; it is not. The skipped block is only what follows the delay slot. Errors are silent: no crash, just a plausible wrong size, a reversed accept/reject, a wrong return value, or an address four bytes off.

**Check / fix:**
- For every branch whose next instruction writes a live register, trace register state on the taken and not-taken paths **separately**, starting both *after* the delay slot. Separate "what decides the branch" (the pre-slot value) from "what survives past it" (the slot's write).
- Decide a loop's accept/reject sense by what each destination *does next* (reaches the epilogue with the slot value intact vs. re-enters the loop head), not by which side looks like the normal path.
- Apply the same check to the function's own return register at its own `jr $ra`.
- A function's last word is often the store in the `jr $ra` delay slot: the boundary is `jr + 8`, not `jr + 4`. Confirm a guessed function start with a real `jal` caller; a "function" that begins with a `nop`/junk single instruction is the tell.
- When citing an address, re-read and decode the raw word there first; better, make the citation a real-corpus test assertion (`expect(word(addr)).toBe(0x…)`).
- In verify scripts, never destructure a word window by position; use an exact-address accessor (`wordAt(img, addr)`) with addresses copied from the transcript.
- When several branches feed one exit, don't trust a careful hand-trace — run the bytes in a tiny scoped MIPS interpreter (`hand-traced-byte-shuffle-needs-independent-resimulation.md`).
- Validate any derived formula against real bytes with an exact-match invariant before shipping it.

**Canonical example:** Valkyrie Profile: Lenneth (PSP) `BOOT.BIN` `fcn.0004aaa4` (PFS header→trailer size): `beqz v1,…` with `sll a0,v0,2` in the delay slot. Read as conditional, "`field28==0` leaves `a0` untouched"; actually `a0 = field28==0 ? entryCount*4 : entryCount*12 + field28`. Verified exactly: `dataSectorCount*2048 + roundUp(result,2048) == fileSize` on the 515,420,160-byte archive.

**Variants (all `valkyrie`, VP1 PSX):**
- *Citation* — Combo Potion's `sb $v0,0x653($a0)` sits at `0x8009a900` in the `jr` delay slot; the `jr` address `0x8009a8fc` was cited in five places, caught only by a probe decoding `03e00008`.
- *Loop sense reversed* — `FUN_8003506c`: `beq $v0,$zero,0x8003547c` with `addu $v0,$t0,$zero` in the slot; the branch target is the epilogue returning the current primitive, so taken = ACCEPT, fall-through = REJECT/continue.
- *Boundary after `jr`* — next functions start at `0x8004740c` and `0x80046f8c`, not `0x80047408`/`0x80046f88` (made twice in one investigation).
- *Positional verify script* — `verify-aoe-splash-damage-fcn800720a8.ts` produced ~13 spurious `[FAIL]`s from miscounted nops/delay slots.
- *Return value* — `func_0x80013DD0`: loop exit `beq` to the sole `jr $ra` with `addiu $v0,$zero,1` in the slot returns `1`, not the `slti` result `0`; an interpreter run caught what the hand-trace missed.

Related: `self-consistent-chain-wrong-unit.md`, `negative-from-addressing-root-not-shapes.md`.

**History:** 6 recorded instances (valkyrie VP-PSP, VP1 PSX) — full log in `_archive/mips-delay-slot-instruction-always-executes.md`.
