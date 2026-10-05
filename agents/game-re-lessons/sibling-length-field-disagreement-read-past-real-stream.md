# When a record has two sibling length-shaped fields that disagree, the byte-count field bounds real decode length — not the sample/element-count field

**When it bites:** a compressed/encoded per-record audio or data stream
has more than one length-shaped field in its header (a sample count *and*
a byte/stream size, or similar), and a fresh decode driven by the
element/sample-count field diffs "correct for a real prefix, then
diverges completely" against a trusted reference decoder — not garbage
from the start, not silence, a clean matching prefix followed by a hard
break.

## What went wrong

Fire Emblem: Three Houses' KTGCADPCM voice-line format (`chimera`
project, `ktgcadpcm.ts`) has a per-channel DSP-info block declaring a
`sampleCount` field, and a separate stream-location table declaring that
same channel's `streamSize` in bytes. A real sample declared
`sampleCount=29002` — needing `ceil(29002/14)*8 = 16576` bytes of 8-byte
ADPCM frames to decode in full — but its own `streamSize` field was only
`14501` bytes, enough for `floor(14501/8)*14 = 25368` samples. Decoding
the full declared `sampleCount` anyway read past the real end of that
channel's stream into unrelated adjacent bytes still inside the shared
source buffer (the *next* voice line's own header, since this decoder
reads directly out of one large multi-entry file rather than a per-stream
truncated copy) and decoded those as if they were more ADPCM frames,
corrupting the tail of the output. A byte-exact diff against the
community's own reference conversion tool + `vgmstream-cli` found the
divergence started at sample 25,424 — matching the `streamSize`-bounded
figure almost exactly (off by under one frame's worth of samples) — not
at sample 0, and not randomly.

Clamping the decoded sample count to
`Math.min(declaredSampleCount, Math.floor(streamSize / bytesPerFrame) * samplesPerFrame)`
fixed it completely: **0/25,368 sample mismatches** against the reference
decoder over the genuinely-valid range. (The reference decoder's own
*extra* samples past that point, visible in its output because its
community-tool source constructed a real fixed-size `.dsp` file rather
than reading from a shared buffer, turned out to be its own EOF-zero-
padding — not real content either decoder should reproduce; the reference
"agreeing" on total sample count doesn't mean it decoded that many *real*
samples.)

## The fix

When a record carries two sibling fields that both bound the same
stream's length in different units (element/sample count vs. byte/stream
size), don't trust the element-count field alone for how much to decode —
compute the byte budget the *other* field actually backs and clamp to
that. This matters specifically when the decode reads out of a large
shared buffer rather than a pre-truncated single-record file: reading past
one record's real extent doesn't fail loudly (no EOF, no bounds error) —
it silently decodes the next record's unrelated bytes as further signal,
producing a plausible-looking but wrong tail. A byte-exact diff against a
trusted reference decoder is what surfaces this ("matches, then diverges
sharply at one point") — a shape distinct from a decoder bug (which
usually diverges immediately or randomly throughout).

This is a sibling problem to `declared-range-field-loose-for-bulk-records.md`
(a record's own declared range can be loose, not tight — there via a
downstream index-reference check; here via a *second*, stricter sibling
field within the same record) and to
`shared-resource-caller-declared-dimension-under-reports.md` (a caller's
declared dimension under-reporting a *shared* resource's real content —
here it's the reverse polarity: one field over-*claims* relative to what
a sibling field actually backs, for a resource that isn't shared at all).
