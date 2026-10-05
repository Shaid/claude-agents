# A field whose values cluster just above 0x80000000 is a flagged small index, not a runtime-patched pointer

**When it bites:** a struct field reads as "implausible `0x8000xxxx`
constants" / "huge negative numbers when read signed" across every sample,
and the write-up forming in your head (or already in the project docs) is
"most likely a runtime-patched pointer or handle slot, not meaningful in the
static file." Also: any field that resolves against a table for only part of
a corpus while a sibling game's copy of the same field resolves cleanly. Also:
a small/simple test file renders or decodes perfectly with a field read as a
plain index, and only a much larger/more complex corpus member later throws
an out-of-range error on that same field — the packed high bits can be
genuinely zero (and thus invisible) on every small sample you happened to
develop against.

## What went wrong

Chimera's FE Warriors docs recorded two of the three fields in G1M's
`BoneBind` record (`{matrixId, clothId, boneId}`) as dead:

> clothId and boneId read as implausible ~0x8000xxxx constants in every
> sample checked and are not used — most likely runtime-patched
> pointer/handle slots, not meaningful in the static file.

That verdict stood for multiple passes and steered a later session away from
the field entirely. **Bit 31 was a flag; the low 31 bits were an ordinary
bone index.** Masking it off made `boneId` resolve for **100%** of 34,758
bindings and immediately explained a rendering bug that had survived several
verification passes. `clothId` likewise turned out to be a real per-palette
group tag with the same flag bit set.

## The tell you can check in seconds

Look at the *spread* of the masked values, not the raw magnitude. Here every
value lay in `[0x80000000, 0x8000FFFF]` — i.e. the low 16 bits varied and the
top 16 were constant. A genuine pointer or runtime handle would not cluster
in the first 64 KB of a 2 GB-offset region across every record in every file;
a small index with a flag bit does exactly that. Other confirming shapes:

- masked values are dense and contiguous from 0 (an index space), not sparse
  and 4/8/16-byte aligned (an address);
- the *same* field in a sibling game / older format version carries the same
  values with the flag bit clear (this corpus's Three Houses files never set
  bit 31 at all, so masking there is a harmless no-op — which is also why a
  one-game investigation missed it);
- masking makes an independent invariant snap from ~0% to ~100% (see
  `stored-bind-matrix-palette-is-a-per-entry-identity-oracle.md`).

## The rule

Before writing off any 32-bit field as pointer-shaped garbage, try
`value & 0x7FFFFFFF` (then `& 0x0FFFFFFF`, `& 0xFFFF`) and re-run whatever
resolution test you have. A high bit is the cheapest place in a 32-bit word
to hide a boolean — "external vs internal", "needs remap", "is a leaf",
"animated" — and engines use it constantly. It costs one line to test and,
unchecked, it converts a live field into a documented dead end that later
sessions inherit and trust. Related: `partial-resolution-rate-is-noise.md`
(the same field failing to resolve for *part* of a corpus), and
`bitfield-spans-multiple-addressable-bytes.md`.

## Second instance: the high word doesn't look like garbage at all — it looks like a correct index, until a bigger file crashes

Confirmed on Dragon's Crown (PS3, `vanille`), decoding `FMBS`'s inner sprite-
model attribute records (`tools/shared/fmbp.ts`, `fmbsPart()`). The `part`
record's `uv` field is a 32-bit big-endian value; reading it whole and using
it directly as the uv-section index worked *perfectly* on the target file
developed against (`character/Barrel00.mbs`, 1,297 parts, uv indices topping
out at 61) — no implausible value, no crash, no hint anything was wrong.
The bug only surfaced when the full pipeline was run over the *entire*
corpus and hit `character/Goblin00.mbs` (13,743 parts, by far the largest
model in the game): `RangeError: uv[262168] out of range (220)`. Unlike
instance one, `262168` doesn't look like a flagged pointer at a glance — it
just looks like a wrong/corrupt index. Histogramming `value >>> 16` across
all 13,743 parts showed only 4 distinct high words (`0`/`1`/`2`/`4`, a small
undecoded selector); masking to `value & 0xFFFF` brought out-of-range hits
from 1,480 to exactly 0, with every resulting low word landing on a real
index. `Barrel00`'s own uv indices never needed the high word at all — the
selector happens to be `0` for every part in that one file, which is exactly
why a single small/simple test target can't be trusted to exercise a
format's full field-packing shape (see also
`format-field-width-unexercised-by-first-corpus.md`, same root cause: a
narrow first corpus can't distinguish "correct" from "coincidentally
correct so far"). **Takeaway: after decoding any packed 32-bit index field
against your first (typically smallest/simplest) test file, re-run the
whole-corpus pipeline before calling it done — the largest/most complex
member is the one likely to expose a packed high word your target never
exercised, and it will surface as a plain out-of-range crash, not as an
obviously-flagged pointer-shaped value.**
