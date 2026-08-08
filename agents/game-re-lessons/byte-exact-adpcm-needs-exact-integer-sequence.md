# Byte-exact ADPCM verification needs the decoder's exact integer sequence, not just its formula

**When it bites:** hand-reimplementing an ADPCM-family codec (PS-ADPCM/VAG,
IMA-ADPCM, MS-ADPCM, XA-ADPCM...) against a reference decoder or a known
coefficient table, and a diff against a trusted oracle (a community decoder
like `vgmstream`, or the console's own documented algorithm) shows small but
real, slowly growing sample-value deviations — not garbage, not silence,
just "close but not identical."

ADPCM decoders are stateful: each sample's decode feeds a running history
(`hist1`/`hist2`) used by the next sample's prediction. Any tiny per-sample
rounding difference compounds, because the *wrong* value — not the correct
one — becomes the input to the next prediction. This makes "looks basically
right" a trap: a plausible-sounding waveform with a formula that matches the
spec's rational coefficients can still diverge sample-by-sample from a real
decoder, because the exact order of operations (when rounding/truncation
happens relative to the addition) is not fully pinned down by the spec's
mathematical formula alone — only by the reference implementation's actual
code.

Concretely, for Sony PS-ADPCM: the textbook-looking float reimplementation
(sign-extend the 4-bit nibble, scale it by the shift factor, add
`coefficient * history` in floating point, round the sum, clamp, and feed
the *clamped* value back as history) produced deviations up to ±49 on a
120,064-sample real voice clip versus `vgmstream`'s own decode — small
enough to sound fine, wrong enough to fail a byte-exact diff. Matching
byte-exact required copying the reference's *exact* integer sequence:

- the nibble is sign-extended and shifted by `20 - shift` (not `shift`
  directly) *before* the predictor term is added — the two contributions
  share one fixed-point scale, they aren't computed and rounded separately;
- the *whole* sum (nibble contribution + predictor contribution) is then
  integer-shifted right by a single fixed amount (8, for PS-ADPCM) as one
  step;
- critically, the **unclamped** running sum — not the clamped 16-bit
  output sample — is what feeds the next sample's history. Feeding the
  clamped value (the "obviously correct" choice, since that's what actually
  gets played) silently desyncs the predictor from the reference the moment
  any sample clips.

**A generalizable shortcut that sidesteps float-rounding ambiguity
entirely:** most public ADPCM coefficient tables are exact rationals with a
small power-of-two-ish denominator (PS-ADPCM's table is exact 64ths). If the
decode's own fixed-point scale factor is a multiple of that denominator
(PS-ADPCM scales the predictor contribution by 256, and 256/64 = 4 exactly),
the *entire* decode — nibble scaling, predictor contribution, and final
shift — is exactly representable in 32-bit integer arithmetic with **zero**
floating-point rounding at any step. This isn't just "cleaner code" — it is
strictly stronger than reproducing a reference's own float-coefficient path
approximately, and several real decoders (including `vgmstream`'s own
source comments on its PS-ADPCM path) explicitly flag their float code as
producing "rounding diffs between implementations." Doing the arithmetic in
exact integers avoids joining that same class of bug rather than chasing it
sample-by-sample.

**Verification bar this unlocks:** with the exact sequence matched, the
diff against the oracle can and should be **0 mismatches across every
sample**, not "close" — confirmed across mono/stereo, looping/non-looping,
multiple real files. Treat anything less than exact-match as evidence the
integer sequence still doesn't match the reference, not as "good enough."
