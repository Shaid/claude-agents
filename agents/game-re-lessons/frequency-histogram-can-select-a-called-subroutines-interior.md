# A PC-frequency histogram can correctly find "the idle loop" and still pick an unsafe re-entry point inside it

**When it bites:** choosing exactly which address, within an already-
confirmed genuinely-infinite idle loop, to use as a boot-injection harness's
force-call re-entry point — especially when the idle loop's own body calls a
subroutine every iteration (not just spins on a flag).

This is a different failure from
`idle-loop-detection-needs-frequency-not-first-repeat.md` (which is about
distinguishing "still in bounded setup" from "genuinely idle" in the first
place). Here, the CPU genuinely has settled into its real, permanent idle
loop — the histogram's *job* succeeded — but the specific address it reports
as "most visited" can still be unsafe to force-call from.

Confirmed on FFIV (SNES)'s AKAOSNES V1 driver: `Main`'s idle loop
(`$0861`-`$08EC`) nests a busy-wait (`$0893`-`$089A`, polling a hardware
counter) that calls a subroutine (`CheckInt`, the interrupt dispatcher)
**every single spin iteration**, not just once per outer loop pass. Since
the busy-wait can spin many times before the counter actually ticks,
`CheckInt`'s own interior instructions — reached via a real `CALL`, with a
return address already sitting on the stack — accumulate *more* PC-visits
over a sampling window than `Main`'s own top-level loop head does. The
frequency histogram (correctly) reported an address inside `CheckInt` as
"most visited." Force-calling a new target from there pushes the harness's
own injected return address **on top of** the return address already
waiting for `CheckInt`'s own `RET` — once that real `RET` eventually fires
(after the injected call's own work completes and normal execution resumes),
it pops the harness's injected address instead of its real caller, and
execution desyncs to a nonsense location.

The failure mode is unusually hard to notice: **not a crash, and not
"quiet"** — every one of 70 test songs constructed without throwing and
rendered exactly `peak=0`, indistinguishable at a glance from "the volume/
pan cold-boot default is still missing" (a real, separate, and much more
common gap in this exact class of harness — see
`session-persistent-channel-state-has-no-cold-boot-default.md`). The
distinguishing symptom (DSP `KON` never observed high at all, not just
attenuated) only shows up once you go looking for it; the decisive
diagnosis came from a plain single-step trace (print `cpu.pc`/`cpu.sp`
before and after every `cpu.step()` immediately following the forced call)
which showed PC landing on a nonsense address (`0x0002`) a short distance
after the injected call's own final `RET`.

**Fix**: when a driver's idle loop is not a flat 2-3 instruction shape
(FFV/FFVI's own `CALL CheckInterrupts; ...; BEQ`, where the histogram's
top hit genuinely is the loop head), don't trust the histogram's top result
blindly — check whether it sits inside a subroutine reached via `CALL` from
somewhere else in the same loop. If the disassembly source names a real,
literal top-level loop-head label (a comment like "start of main loop," or
a `JMP`/branch back to a fixed address at the loop's own tail), target that
address **directly** instead of the histogram's output, and confirm safety
empirically: single-step a forced call from that address and verify it
reaches its own natural return (or the loop head again) at a consistent
step count, with the stack pointer unchanged before and after. A histogram
is still useful for finding the loop *region* in an unfamiliar driver with
no available source, but the exact re-entry point within it needs this
extra check whenever the loop's body contains a real `CALL`.
