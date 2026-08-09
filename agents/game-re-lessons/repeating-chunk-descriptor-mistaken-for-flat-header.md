# A confirmed fixed-size "header" may be one instance of a repeating chunk descriptor, not a one-off file header

**When it bites:** a fixed-size sub-header/descriptor was confirmed correct
(e.g. via cross-sample byte-divergence — see
`cross-platform-decode-oracles.md`/Method §4 for the technique) but the
payload's overall byte-count arithmetic still isn't fully accounted for
after subtracting it — there's a suspiciously large "template/reserved,
byte-identical across every sample" region inside it, and/or a "family
constant" field you've already measured as real and byte-exact-consistent
across samples but haven't yet explained semantically.

Confirmed on Valkyrie Profile 2: Silmeria (PS2, `~/Development/valkyrie`):
an earlier pass on the game's `"FIS\0"` texture format correctly used
cross-sample byte-divergence to pin a 256-byte "sub-header" (real technique,
real result — bytes 0-0x0F identical across same-length-different-content
samples, dense divergence starting exactly at 0x100). It then assumed pixel
data started immediately after those 256 bytes, and read two of the
descriptor's own fields (`0x1C`, `0x20`) as an unexplained "family constant"
and a "format tag" that happened to correlate with image width. Both were
real, correctly-measured, byte-exact-consistent fields — just misinterpreted
in isolation. A `re-codebreaker` escalation found the actual shape: the
256-byte descriptor is a **generic, repeating** PS2 GS texture-transfer
chunk header (`descriptor : 256 bytes` + `data : chunkLengthField * 16
bytes`, looped), and every real payload contains **exactly two** such
chunks back-to-back — chunk 0 is a colour-palette (CLUT) chunk, chunk 1 is
the actual indexed image (its own 256-byte descriptor, then real pixel
data). The "family constant"/"format tag" fields were the CLUT's byte size
and a value derived from it — real fields, wrongly read as belonging to a
single flat header instead of to a second, later chunk instance that reuses
the identical 256-byte descriptor shape.

**The generalizable move**: once a fixed-size header/descriptor is
confirmed (by divergence comparison, field-consistency checks, or any other
method), before assuming "then the rest is payload," check whether **the
same struct shape recurs again later in the same buffer** — walk forward by
the confirmed header size + whatever length field it declares, and see if
another instance of the identical byte pattern (same constant/template
bytes at the same relative offsets) appears there. A large "template,
byte-identical across every sample" region inside a confirmed header is a
specific tell: it's cheap for a format to reuse one descriptor struct for
several different resource types/chunks in the same container (a palette
chunk and an image chunk sharing one header shape is a common pattern for
GPU-adjacent texture formats specifically, but the principle isn't
GPU-specific), and a chunk-walk model explains that reuse for free where a
flat single-header model has to leave it as "unexplained padding."
