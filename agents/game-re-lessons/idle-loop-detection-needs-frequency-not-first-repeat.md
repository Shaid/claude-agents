# Detecting a CPU emulator's "settled into steady state" point needs both a measured warmup floor AND frequency sampling — neither alone is reliable

**When it bites:** building a boot harness that runs an emulated CPU from
its real reset/init entry point and needs to detect when it has finished
one-time setup and settled into its permanent idle/main loop (so a call can
be safely injected there).

> **Correction, same investigation, later in the same session**: an earlier
> version of this lesson recommended frequency-based detection alone as
> sufficient, citing a specific address/hit-count as the confirmed real
> idle loop. That specific claim was wrong — the address it named turned
> out to be a *different*, still-bounded (if very high-iteration) real
> hardware-timing spin loop, not the true permanent idle loop, and the
> harness that "successfully" injected a call there went on to produce
> silently corrupted output for a different, harder-to-notice reason (see
> below). The corrected fix is below; this file replaces the earlier one
> rather than living alongside it.

Two independently-failing detector shapes, confirmed on the same real
target (FFVI SNES's AKAOSNES V4 driver):

1. **"Stop at the first PC that repeats within a short lookback window"**
   fails immediately — a driver's own `Init`-style boot code almost always
   contains genuine but *finite* loops of its own (a RAM zero-fill, a table
   copy), and a short-lookback detector locks onto one of these long before
   the CPU ever reaches the real idle loop. Confirmed: a 400-instruction
   lookback window locked onto an address inside `Init`'s own low-RAM
   zero-fill.
2. **"Sample PC-visit frequency over a long window, pick the most-visited
   address"** is a real improvement (a bounded setup loop generally can't
   accumulate as many hits as a truly-infinite idle loop over the same
   window) but is **not sufficient on its own** if `Init` itself contains a
   *bounded-but-very-high-iteration* loop that's still running when the
   sampling window starts — a real hardware-timing spin-wait (`Init` here
   waits on a hardware timer for a value read from a register that happens
   to be `0` at cold boot, forcing an 8-bit counter to wrap all the way
   around: 256 timer ticks, ~4.1 real seconds at the target's own real
   clock rate) dominates a frequency histogram exactly as convincingly as
   the real idle loop would, for the same underlying reason (it's real,
   it's bounded, and it just happens to have a very large bound). A forced
   call injected at this loop's head **does not obviously fail**: if the
   `Init`→idle-loop transition happens to jump cleanly regardless of
   exactly where in "the tail of `Init`" you resume it from, the driver
   *looks* like it's running completely normally afterward — the actual
   symptom was a handful of `Init`'s own very last, skipped instructions
   (setting a global master-volume-style register) leaving one piece of
   state at its earlier cold-boot default, silently zeroing all further
   *output* while every other subsystem it fed (envelopes, pitch, gating)
   ran correctly. This is a much harder failure to notice than the first
   detector's obvious corruption — it can pass every "is the harness
   plausibly executing real code" check while still producing wrong final
   results.

**Fix**: run a fixed, *unconditional* warmup budget — measured directly
against the real target (instrument the harness once to find exactly which
cycle `Init` first reaches its real idle loop, then set the budget
comfortably past that measured point) — **before** starting any frequency
sampling at all. Only start the histogram once you're confident real
one-time setup has fully finished; the histogram's job is then just to
pinpoint the *exact* loop head within an already-idle CPU, not to
distinguish "idle" from "still booting" in the first place. Don't trust a
frequency-sampling result as proof of having reached steady state merely
because *some* address dominates the window — a dominant address is
consistent with either the real idle loop or a slow-but-bounded setup
phase, and only a measured, real-target-specific warmup floor
(re-derived per target, not guessed) tells the two apart.

**Even once you've genuinely reached the real idle loop**, the histogram's
top address still isn't automatically a *safe* one to force-call from if
the loop's body itself contains a real `CALL` to a subroutine — see
`frequency-histogram-can-select-a-called-subroutines-interior.md` for that
separate, later-stage failure (the histogram's job succeeded; the specific
address it named is still unsafe).
