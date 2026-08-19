# Structurally-parallel LFO VCMDs can apply their signed delta asymmetrically per consumer

**When it bites:** a driver has two (or more) structurally-parallel,
LFO-driven VCMDs that share the same rate-calculation/enable/direction-byte
encoding (e.g. vibrato and tremolo sharing one "amplitude+cycle-length"
setup routine) but feed two *different* downstream registers (pitch vs.
volume, pan vs. something else) — about to assume both application sites
treat the shared signed accumulator identically (symmetric add/subtract).

## What happened

FFVI's (SNES) AKAOSNES V4 driver computes vibrato and tremolo through the
literal same shared rate-calculation and triangle-wave-ramp routines (same
6-bit amplitude, same direction-mode byte, same accumulate-and-reflect
mechanic) — everything about their *generation* is identical. But their two
*consumers* are not symmetric: vibrato's consumer (`UpdateChanFreq`) applies
the signed accumulator to the pitch register with a plain unconditional
16-bit add — genuinely bidirectional. Tremolo's consumer (`UpdateChanVol`)
tests the accumulator's sign bit via `ASL A` (shifting it into carry) then
`BCS <skip>` — meaning a **negative** delta is silently dropped entirely
(no volume change), not subtracted. The practical effect: a "negative"
direction-mode tremolo is near-inaudible on real hardware (its LFO value is
always ≤0, so almost every tick gets skipped), while the *identical*
direction-mode setting on vibrato produces a fully audible downward pitch
sweep. Nothing about the shared generator code hints at this — it only
shows up by tracing each consumer's own instructions.

## The fix

Don't infer a downstream consumer's behavior from a sibling consumer that
shares the same upstream generator, even when the generator code is
byte-identical or near-identical between the two. Trace (or byte-diff) each
consumer independently — a volume-target consumer clamping/dropping negative
deltas (because "negative volume" isn't representable) while a
pitch-target consumer applies them freely is a plausible, real asymmetry,
not a coincidence specific to any one game. When documenting/implementing a
"shared LFO, two mix points" mechanism, call out per-consumer clamping
explicitly rather than describing the whole feature with one formula.
