# A harness's blank screen or frozen clock is an unmodelled hardware wait, not unreached game state

**When it bites:** a CPU-emulation harness runs real code without hanging
or crashing, but a page draws blank, an animation or in-game clock never
advances, or a probe reports "the game just idles" with every state table
still zero.

Games wait on display hardware constantly — a `btst` on an
interrupt-request register's vertical-blank bit, a compare against a
raster/beam-position register, or an OS call that polls one. A harness
that maps those registers as plain RAM returns a constant, so the wait
condition never becomes true and the code spins there forever. The
harness itself does **not** appear hung: its outer loop and interrupt
injection keep ticking, cycle counts keep climbing, nothing faults. It
simply never reaches the next phase, which is indistinguishable from
"this screen is never drawn" / "these records are never populated" — so
it gets written up as a finding about the *game*, and everything
downstream of the stalled phase is reported as empty, dead or inert. A
register-save omission in the stub's VBL path corrupts decoder output in
the same invisible way.

**Check / fix:** before drawing any conclusion from an empty table or a
blank render, profile the PC over a window (not a single sample). A tiny
hot loop whose body reads a custom-chip/MMIO address or calls a library
entry is a *wait*, not idleness: look the address up and model it — hold
the vertical-blank interrupt bit pending once per emulated frame, make a
beam-position read return a value that lets the compare fall through (a
constant past the threshold, or a sweeping counter), stub the OS beam
call. Then **re-run every earlier "nothing happens here" conclusion**:
one such fix typically unlocks several at once, and the stale negatives
are the expensive part, not the loop. This is the display-hardware
sibling of `coprocessor-status-byte-all-reads-no-writes.md` (a
shared-RAM poll with no writer in the emulated CPU's own code) and is
distinct from `idle-loop-detection-needs-frequency-not-first-repeat.md`,
which is about recognising the *real* idle loop once the waits are
already modelled.

**Canonical example:** Deuteros (Amiga, `methanoid`): the `live_probe`
Musashi harness drew a blank shuttle bay and its in-game clock never
moved, and the docs recorded "idles at screen 0 / shuttle bay blank" as
game behaviour across a whole pass. The game's vsync wait spins on
`VHPOSR` and `INTREQR` bit 5 (`VERTB`), neither of which the harness ever
set. Raising INTREQR bit 5 each VBL and stubbing the `VBeamPos` reads
with a constant made the wait fall through; the bay, every sub-screen and
the clock all came alive, superseding the earlier conclusions and
unblocking a full UI-driven build/launch/flight trace.

**History:** 1 recorded instance (`methanoid`).
