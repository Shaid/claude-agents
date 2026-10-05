# A corpus-wide "every record's own raw minimum is exactly 0" invariant, plus one literal contiguous row in the raw data, outranks "produces clean composites" for signed-vs-unsigned bitfield decisions

**When it bites:** a packed bitfield's sub-range (a screen-space delta, a
tile coordinate, a small signed-looking offset) was decoded as two's-
complement signed because that "looked reasonable" and produced
non-corrupted-looking output, but the decision was never cross-checked
against a second, independent oracle — especially when the composited/
rendered result still has a visible defect (a duplicated-looking half, a
big unexplained gap, disconnected fragments) that got attributed to
something else.

## What happened

Confirmed on Parasite Eve (PSX, `parasite` project): a tile-scatter
background compositor's per-tile placement word packed two 10-bit
"delta" fields, and the shipped decoder read them as two's-complement
signed (`(val & 0x1ff) - (val & 0x200)`), because it produced plausible-
looking, non-crashing composited PNGs corpus-wide. But a few packages
rendered as two disconnected halves with a large black gap between them —
symptomatic-looking but not conclusively diagnosed as a sign bug on its
own (a user report just called it "artifact").

Two cheap, corpus-wide, purely-statistical checks settled it before any
disassembly:

1. **Per-record raw minimum is always exactly 0.** Across every active
   record in the whole corpus (2,078 triggers, 414 packages), the
   un-sign-converted minimum of both 10-bit fields was **exactly 0, zero
   exceptions**, while raw values legitimately ranged up to 768 — far past
   the signed 10-bit threshold of 512. A real two's-complement field would
   not produce a *universal* minimum of exactly 0 across every single
   record; a field that's genuinely "this record's own tile grid, always
   flush against its own local origin" would.
2. **A literal contiguous raster row in the raw data.** Dumping one large
   record's raw tile list directly (not sign-converted) showed many tiles
   sharing the same raw Y value with X running smoothly 0,16,32,...,304 —
   an unmistakable full-width horizontal strip of adjacent 16px tiles. A
   two's-complement reading of that same Y value (768) would put it at
   768−1024=−256, nonsensically split away from the rest of that same
   row's own tiles, which sit far below 512. A genuine, physically
   contiguous raster row only exists under the unsigned reading — this is
   positive structural evidence, not just "the composite doesn't look
   broken."

A `ghidra-disasm` trace of the real decode instructions later confirmed
this at the byte level (every unpack used a logical/unsigned shift, never
an arithmetic/sign-extending one), but the corpus-wide statistical checks
above already settled the question for free, before touching a
disassembler.

## The fix / general rule

Before trusting (or leaving un-cross-checked) a signed-vs-unsigned reading
of a packed field:

1. **Compute the per-record minimum of the raw (un-converted) value across
   the whole corpus.** A universal, zero-exception minimum of exactly 0
   is a strong tell for "unsigned, locally-originated" — a real signed
   field has no structural reason to always bottom out at the same
   constant.
2. **Look for a literal, smooth, physically contiguous structure** (a full
   raster row/column, a monotonic ramp, an unbroken index run) somewhere
   in the raw values. If treating the field as signed would tear that
   structure apart at the sign boundary (half the row becomes a huge
   negative number, disconnected from the rest), that's decisive —
   stronger than "the rendered output looks fine," which a sign bug can
   often survive by accident (bounding-box math absorbing the corruption
   into an oversized-but-still-nonzero canvas).
3. Treat "produces clean composites" alone as **not yet a confirmed sign
   convention** — it's the same class of weak evidence `single-outlier-
   defeats-bbox-camera-fit.md` warns about (a render can look "fine" while
   silently absorbing a real structural error into unused canvas space).
   A visible-but-unexplained artifact (duplicated content, a big blank
   gap, split fragments) is a specific reason to suspect exactly this kind
   of unverified convention, not something else.
