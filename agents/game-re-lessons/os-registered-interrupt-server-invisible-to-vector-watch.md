# A bare-CPU harness that watches the interrupt vector cannot see a handler registered through an OS library call

**When it bites:** a hand-rolled emulator harness (Musashi/unicorn-style,
no OS stubs) is used to settle "is this driver/ISR ever installed?" — it
watches the autovector slot or the hardware registers, reports the vector
still all-zero at run end, and some in-data gate (a header pointer = 0, an
unset enable byte) appears to corroborate it. The write-up then closes the
subsystem as dead: "audio is permanently silent in this state", "the
handler is never installed", "the records behind it are unreachable".

A game that runs **under an OS** does not write the vector itself; it hands
a handler to the OS and the OS dispatches it. On Amiga/exec that is
`AddIntServer(INTB_VERTB)` — build an `Interrupt` node (`ln_Type` 2, a
priority, a name pointer, a code pointer) and `jsr (-$A8,A6)`. The
autovector is never touched by the game's own code, so a vector watch over
a stubbed or absent exec is structurally blind to the registration. The
same hole exists for `SetIntVector`, `AddTask`, `OpenDevice`/`DoIO`,
`AddSoftInt`, and for every non-Amiga equivalent (a DOS `INT 21h/25h`
handler install, a console-SDK `RegisterHandler`/`CreateThread` callback,
a BIOS/kernel timer-callback registration): the handler address exists only
inside a structure the game passes out, never in a slot the harness watches.

**The second half of the trap is where the call site sits.** The
registration frequently lives on an *unconditional* path that runs
**before** the gated branch under analysis, so the gate everyone found is
gating a different, later subsystem (here: a music tracker) while the thing
declared dead (sample playback) was already wired up upstream. A gate that
provably never fires is only evidence about what that gate controls.

**Check / fix:**
- Before accepting any "never installed" verdict from a bare-CPU harness,
  census the init path for OS registration idioms — on 68k/Amiga grep the
  disassembly for `jsr (-$a8,a6)` / `-$ae` (Add/RemIntServer),
  `-$a2` (SetIntVector), `AddTask`, `OpenDevice`, and resolve A6's
  provenance; elsewhere, for whatever the platform's "give the OS a
  callback" call is. An OS-call census is cheap and answers the question
  statically.
- Walk **every unconditional call preceding the gate**, not just the gated
  branch. Name what the gate actually controls.
- A harness may stand in for the OS (call the handler yourself every N
  instructions), but only arm that stand-in once the game's own code has
  reached the registration PC — otherwise you have injected the very state
  you set out to measure
  (`differential-oracle-blind-to-harness-injected-state.md`).
- Then prove playback/effect with a **null control**: force the handler's
  own enable flag to 0 and confirm the output goes to zero.

**Canonical example:** Deuteros (Amiga, `methanoid`). A cold-boot
bare-Musashi probe reported vector `$6C` unwritten with zero PCs in the
driver's range — true, and the matching gate (`$2126A` = 0) really does
skip `jsr $22330` at `$2133C`. Both facts were right and the conclusion
("sound is closed in state 0") was wrong: `$2132E jsr $20888` runs
**unconditionally, one instruction earlier**, builds the `Interrupt` node
at `$2086A` and calls `AddIntServer(INTB_VERTB)` at `$208B4`. With the
harness standing in for exec only after the game reached `$208B8`: 70
natural dispatches, 64 distinct non-baseline Paula (LC/LEN/PER/VOL) tuples
matching the sample table, 20 PCM records shipped (lag-1 autocorrelation
0.53-0.97 vs ~0 shuffled), and the null control (enable byte forced to 0)
gave 0 tuples. The gate turned out to control only the tracker path.

**A disassembly misread can manufacture the same false negative.** In the
same subsystem a "0 callers" result came from data at `$22AB6` decoding as
`ori.l`, which swallowed the real entry point at `$22AB8` that the project's
own op-table already named. A zero-caller census over a region whose entry
offset you inferred from linear disassembly is worth re-running one word
later (`m68k-reset-vector-is-opcode-space-other-vectors-are-data-space.md`
family).

**History:** 1 recorded instance (`methanoid`).
