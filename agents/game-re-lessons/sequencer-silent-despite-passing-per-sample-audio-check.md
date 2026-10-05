# A sequence/track renderer built on confirmed-good samples can still render >99% silent when notes outlast the underlying sample

**When it bites:** building a debug listening-check renderer (or any
downstream consumer) on top of already-confirmed, non-degenerate audio
samples (passed RMS/distinct-sample-count/lag-1-autocorrelation checks
individually), where the samples are short relative to the note durations a
sequence-body decoder assigns them — most commonly a hardware ADPCM/PCM
sound format with a loop-repeat convention (a short "seed" waveform meant to
be repeated by the sound chip's own hardware loop flag for as long as a
note is held, rather than one complete recording per note).

Confirmed on Final Fantasy VII (PSX field-BGM renderer, `siren` project): a
first-pass renderer decoded each instrument's confirmed-real ADPCM range
once per note and wrote it starting at the note's onset, same as an
already-working sibling renderer for a different AKAO sub-format. The
result passed every per-sample audio-quality check (the underlying decoded
waveforms individually had healthy RMS, distinct-value counts, and
autocorrelation), yet the rendered mix was **>99% near-silent samples**
(measured: 99.6%/97.9% of int16 samples below a `|s|<200` threshold across
two real 15/16-track renders). Root cause: most real instrument records
were only 1-2 ADPCM blocks (28-56 decoded samples, a few milliseconds) —
almost certainly a hardware loop-repeat seed — while note durations
(computed from confirmed tempo/tick data) routinely ran into the hundreds
or thousands of samples. Playing the seed once and leaving the rest of the
note's allocated duration untouched (silence) is exactly what a linear,
non-looping renderer does with no bug in either the sample decode or the
duration computation — the defect is purely in *how the two are combined*.

**Why the existing checks didn't catch it:** every established audio-
quality oracle in this project's convention (RMS, distinct-sample count,
lag-1 autocorrelation) is scoped to one decoded *sample*, not to a
*rendered mix* built by sequencing many samples over time. A statistical
check on the input says nothing about whether the thing built on top of it
is silent in aggregate.

**Fix:** when validating a sequencer/renderer (not just the underlying
sample decoder), compute a **mix-level** statistic separately from the
per-sample one — e.g. the fraction of rendered samples below a small
threshold, or overall RMS of the full mixed buffer — and sanity-check it
against the source material's genre (background music should not be >90%
silent). If most instrument records are short relative to typical note
durations, the two are being combined wrong; a cheap, honestly-labeled
approximation (tiling/repeating the short buffer to fill the note's
duration, `buffer[i % buffer.length]`) is far closer to real behavior than
playing it once, even though it introduces its own audible artifact (a hard
non-crossfaded seam every repeat, raising the zero-crossing rate/spectral
noise floor) that should be documented as a known limitation rather than
silently accepted as "good enough because the sample decode was confirmed."
