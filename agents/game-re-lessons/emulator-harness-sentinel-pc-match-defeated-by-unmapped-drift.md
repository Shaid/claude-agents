# A bare-CPU-core harness's "PC == sentinel" completion check silently fails under a large per-call cycle budget

**When it bites:** building or reviewing a bare-CPU-core (musashi or
similar) harness that enters a subroutine directly at PC — not via the
game's own call chain — with a pushed sentinel return address, and checks
`PC == sentinel` after each `execute(N)` call to detect the subroutine's own
`rts` completing. Especially when the run silently hangs or times out with
a large per-call cycle budget (needed for performance) but completes fine
with a small one (near 1 instruction/call) — before assuming a real
control-flow bug, corrupted stack, or engine misbehavior.

This is a distinct failure mode from
`emulator-harness-pc-range-completion-defeated.md` (a *range* check
defeated by real, environment-aware cleanup code wandering back into the
watched range via stroboscopic sampling aliasing) — no wandering-back-in
and no real cleanup code is needed to trigger this one; it happens on a
single, correct `rts` with nothing else going on.

The sentinel address is deliberately unmapped (e.g. above the emulated
memory array's bound, so reads return 0). The instant `rts` pops it into
PC, the CPU keeps "executing" that all-zero memory: on 68000, opcode
`0x0000` is `ORI.B #0,D0`, a real, harmless, 4-byte instruction (2-byte
opcode + 2-byte immediate) with no stack effect. PC drifts steadily upward
through unmapped address space, 4 bytes at a time, for the *rest of that
`execute()` call's cycle budget* before control returns to the check. With
a large budget (e.g. 200,000 cycles/call), by the time the check runs PC
has already wandered far past the exact sentinel value — the check never
fires, and the drift can eventually carry PC back into the harness's *own
loaded binary* at an unrelated address, executing real code there with
whatever register state happened to survive (data/address registers are
untouched by the zero-opcode drift). Confirmed on Powermonger (Amiga): a
`$F860` terrain-gen harness with `CHUNK_CYCLES=200000` ran the full 400M
cycle safety-cap budget and ended up executing a genuine Amiga CIA-ICR
hardware poll loop elsewhere in the loaded RUN_PROG binary (which spins
forever with no real hardware behind it in the harness), while the
identical setup with `CHUNK_CYCLES=20` completed correctly in ~7.5M cycles.
Diagnosed by comparing a small-step trace (worked) against large-budget
chunked runs (didn't), then instrumenting the memory-write callbacks to log
writes near the stack/sentinel region — which showed the sentinel word was
never overwritten (ruling out stack corruption) and that PC's logged value
at the first post-return check was already sentinel+offset, climbing by
roughly one cycle-budget's worth of 4-byte "instructions" each subsequent
chunk.

**Fix:** don't gate completion on PC at all — gate on **SP (A7) returning
to exactly its pre-call starting value**. A7 is untouched by the phantom
zero-opcode drift (`ORI.B` has no stack effect), so once the real `rts`
pops the sentinel and SP returns to its starting value, SP *stays* at that
exact value no matter how far PC subsequently wanders — making an
A7-equality check robust regardless of per-call cycle budget size, with no
performance/reliability tradeoff. This generalizes to any "enter a
subroutine directly at PC with a pushed return-address sentinel" harness
pattern; a harness that instead lets the whole program run via its own
internal call chain (never checking an exact PC-vs-sentinel match) doesn't
need this fix, but any harness using the sentinel-PC-match idiom directly
is at risk.
