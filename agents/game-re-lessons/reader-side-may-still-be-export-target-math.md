# A format tool's "reader" module can still be export-target math, not a hardware model

**When it bites:** about to port a fan MIDI/soundfont/DLS-conversion tool's
*reader*-side source (the part that parses the game's own sequence/instrument
format, as opposed to its exporter that writes `.mid`/`.sf2`/`.dls`) as
ground truth for a bit-accurate hardware audio decode — especially anything
computing cents, dB, or a 0-127 CC-style range from a raw driver byte.

## What went wrong (and what didn't)

Auditing ceres's FFVI AKAOSNES V4 sequence renderer against
`vgmtrans/vgmtrans`'s complete `AkaoSnesSeq`/`AkaoSnesInstr` reader (not just
its already-known-lossy MIDI exporter), the sequence-command dispatch code
(`AkaoSnesSeq.cpp`'s `readEvent`) genuinely does parse the real byte stream
correctly — VGMTrans's project structure separates "reader" (`formats/`) from
"exporter" (MIDI/DLS/SF2 writer) cleanly at the file level, and the reader
files *do* contain real, checkable facts (opcode tables, argument byte
counts, bit-packing for a few genuinely-just-forwarded fields).

But **the vibrato/tremolo/pan-LFO/pitch-slide/pitch-envelope code living in
those same "reader" files** (`AkaoSnesModulation.cpp`, `AkaoSnesTrackPitch.cpp`)
turned out to be pure MIDI/SF2-export math throughout — cents-per-semitone
log2 conversions, dB attenuation curves, and 0-127 MIDI-CC-range scaling, with
no fixed-point arithmetic resembling the real driver's actual DSP-register
formula (which this project had independently traced from `SPCCode` for the
*pitch* VCMD in an earlier pass: a 12-entry table lookup + integer octave
shift, nothing resembling `log2`/cents anywhere). The file/module lives on the
"reader" side of the tool's own code split, but its actual job is still
"produce a number an export target (MIDI/SF2) can consume," not "reproduce
what the real hardware register receives." Reading it did not make these
VCMDs any more tractable to implement — correctly left as no-ops rather than
ported, since implementing MIDI-approximation math and confidently labeling
the result "ported from a reader, should be accurate" would have repeated the
exact mistake this same codebase had already been burned by twice before
(a volume-byte range and a pitch formula, both earlier pulled from VGMTrans's
*exporter* conventions and found wrong against real ROM bytes).

## The fix

A tool's own file-level "reader vs. exporter" split is not a reliable proxy
for "hardware-accurate vs. export-approximation" — check what a specific
function actually computes (raw bit masks/table lookups vs. logs/cents/dB/
CC-range math), not which directory or class it lives in. Any function whose
final step is `log2(...)  * 12.0` (cents), `-20 * log10(...)` (dB), or a
`clamp(..., 0, 127)` MIDI-range squeeze is export-target math regardless of
which side of the tool's own module boundary it's filed under, and should be
treated with the same skepticism as literal exporter code — a useful
structural/behavioral hint (which VCMD exists, roughly what it does
semantically) but not a source to port formulas from without an independent
ROM-byte trace.

> **Correction (a later session on the same project):** the verdict above —
> "vibrato/tremolo/pan-LFO/pitch-slide are pure MIDI/SF2-export math, no
> hardware model" — was itself overstated. That pass read only
> `AkaoSnesModulation.cpp`/`AkaoSnesTrackPitch.cpp`; it never opened
> `AkaoSnesTrackLfo.cpp`, a **third sibling file in the same reader
> directory**, which turned out to contain real, version-aware
> (`AKAOSNES_V1`-`V4`) decoding of the driver's actual internal LFO rate/
> depth/frame-timing parameters — genuine hardware modeling that the
> export-math files' final cents/dB conversion step sits *downstream* of.
> **The fix above (check what a function computes, not which file/class it's
> in) is still correct and was reapplied successfully** once the missing
> file was read — but it wasn't applied broadly enough: two files out of a
> reader directory's several is not "the whole reader," and a "pure export
> noise, no hardware model anywhere in here" verdict needs the *entire*
> reader directory audited, not just the files a first pass happened to open
> (e.g. because they were the ones an earlier, narrower pass already cited).
> Before writing off a whole VCMD family as unimplementable from a reader
> source, list every file in that reader's own directory and confirm each
> was actually opened — a sibling file you didn't read can hold the real
> model. See `adjacent-cache-slot-elimination-identifies-register.md` and
> `parallel-lfo-vcmds-may-clamp-asymmetrically.md` for two further techniques
> that came out of the corrected pass.
