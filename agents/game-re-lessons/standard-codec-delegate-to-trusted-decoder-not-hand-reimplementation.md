# A confirmed standard (non-game-specific) codec is a delegate-to-a-trusted-decoder case, not a hand-reimplementation case

**When it bites:** a container/header format has already been confirmed
(structurally, field-for-field, against a public third-party spec) to be a
**standard, publicly-documented, non-game-specific codec** (video, audio,
image, archive — something with an existing mature open-source decoder,
not an in-house/proprietary format invented for this one game), and the
next step is producing an actual pixel/sample-level decode to meet the
verification bar. A hand-reimplementation attempt (transcribing a Huffman
table, a bitstream layout, or similar detail from prose documentation)
either hasn't been tried yet, or has just hit a **real decode failure**
(an actual parse/bounds error on real content — not merely "feels risky"
or "looks slightly off").

Confirmed on Valkyrie Profile (PSX): a large family of `raw-other` TOC
slots were confirmed, field-for-field against the public `m35/jpsxdec`
`PlayStation1_STR_format.txt` spec, to be standard PSX "STR" MDEC video —
magic, chunk/frame counters, dimensions, and version fields all matched a
third-party reference exactly. The natural next step per the verification
bar ("don't stop at looks right — decode a sample") was building an actual
MDEC decoder: bitstream reader, DC/AC Huffman tables (~111 variable-length
codes), IDCT, YCbCr→RGB. A hand-rolled Python implementation, built from a
mix of trained recall and prose-summarized web fetches of the spec,
**failed with a real "no VLC match" parse error** on genuine frame content
(it had spuriously "succeeded" on an unrepresentative near-black opening
frame first, which masked the bug on the first attempt). Rather than
continuing to debug ~111 hand-transcribed bit patterns against a spec that
several fetches had already failed to quote completely and verbatim, the
sectors were instead wrapped into a synthetic container `ffmpeg`'s own
`psxstr` demuxer expects (a fake CD-XA sector wrapper — the one piece
VALKYRIE.BIN's own storage format had stripped away) and handed to
**ffmpeg's real, independently-implemented, already-correct `mdec`
decoder**. This worked immediately once the synthetic wrapper's one
required field (a CD-XA submode byte) was corrected by reading ffmpeg's
own demuxer source rather than guessing — producing real, coherent,
temporally-consistent decoded video frames, confirmed via ffmpeg's own
stream-info output explicitly naming the `mdec` codec (not a generic
fallback path).

**The generalizable move**: once a container is confirmed to be a
*standard* format (not the game's own invention), a hand-reimplementation
attempt that hits a genuine decode failure is a signal to stop patching
and check whether a mature, trusted, independent tool already implements
the *standard* — not just the sibling technique's own reimplementations
(fan decoders for the exact game). `ffmpeg`, established emulator cores,
and reference libraries (libpng, a standard MPEG/JPEG decoder) routinely
qualify. Getting the trusted tool to accept the bytes may require
synthesizing a container layer the game's own storage format stripped away
(here: fake CD-XA framing) — that reconstruction is a much smaller, safer
surface area to get right than an entire bitstream codec, and any mistakes
in it fail loudly (the tool rejects the file) rather than silently (a
subtly-wrong Huffman table can produce plausible-looking but wrong pixels
for some frames while failing outright on others). This is the general
form of Method §5's "when hand-reimplementation fails, emulate" — but
applies specifically to *standard* formats, where the answer is "use an
existing independent implementation of the standard," not "run the game's
own code."

**The boundary — not every standard codec needs this.** The signal above
is complexity/error-surface (Huffman/VLC tables, adaptive bitstreams,
anything with dozens of magic constants transcribed from prose), not
"standard format" by itself. A small, fully public, deterministic
fixed-function block codec is fine to hand-roll directly rather than
shelling out to a trusted tool — confirmed on NieR:Automata (PC)'s texture
pipeline (`flower` project): Microsoft's DDS container + BC1/BC3 (S3TC/
DXT1/DXT5) 4x4-block decompression (`tools/shared/dds.ts`) is a ~30-line,
fully spec-fixed algorithm with no adaptive tables and no ambiguity, and
was hand-rolled directly from the public spec rather than reached for a
third-party npm decoder — verified correct via byte-exact mip-chain/
cubemap-face-layout size invariants against real files (not just "looks
right"), the same verification-bar discipline this lesson's PSX MDEC case
used, just without needing the delegation step. The distinguishing
question before choosing either path: does getting this decode right
require faithfully transcribing a large, error-prone table or an adaptive
bitstream state machine (delegate), or is it a small fixed-size lookup/
interpolation with no hidden state (hand-roll is fine, and keeps the
project dependency-free)?
