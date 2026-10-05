# `undefined`/`NaN` silently turns a `while(x !== target)` decrement loop into an infinite hang

**When it bites:** porting a decoder whose loop-termination shape is
`while (x !== 0) { x--; ... }` or `for (;;) { x--; if (x === target) break;
... }` (common in hand-transliterated C/C#/68k decompilers), and either (a)
a hardcoded numeric lookup table the loop indexes into was hand-transcribed
from an external source and might be shorter than intended, or (b) the
decoder is being probed with adversarial/out-of-range input (e.g. the
"decode sequential ids until it throws" technique for finding a real
directory's element count) and a count/size field read from the data
itself feeds an allocation or another loop bound.

`undefined - 1 === NaN`, and `NaN !== 0` / `NaN !== -1` are always `true`
— so once a lookup miss or an already-corrupted variable goes `NaN`, a
decrement-until-target loop never reaches its exit condition and spins
forever instead of erroring. This is a sibling of
`typed-array-silent-oob-read.md` (same JS root cause — no bounds checking
on `Uint8Array`/plain-array indexing) but a different, more disruptive
failure *shape*: that file covers "invalid input silently decodes as if
valid"; this one is "the process hangs with zero output and no exception,"
which is harder to triage because there's no stack trace or wrong-looking
result to chase — just a stuck process.

## Two confirmed manifestations (Bard's Tale Amiga codec port, `crawl`)

1. **Truncated hardcoded constant table.** `tools/shared/bardstale-codecs.ts`
   ports a 256-entry log2-bucket lookup table (`_hard2` in the C# source)
   used to decode LZ77 match lengths. Two independent hand-transcriptions
   of the same external source text (one in a throwaway debug script, one
   in the real module) each came out a *different* wrong length — 247 and
   248 entries respectively, both silently short of the real 256. A
   position-decode loop (`for(;;){ var10--; if (var10===-1) break; ...}`)
   fed by `HARD2[varE] - 2` spun forever once `varE` landed on one of the
   missing tail indices. Root-caused only by adding an explicit iteration
   cap to a debug harness (which threw "pos loop stuck" instead of
   hanging), then re-parsing the *original* source text with a script that
   counted comma-separated values — not by eyeballing the transcription a
   second time (see `hand-transcribed-generated-table-drifts-from-source.md`
   for the sibling failure mode where a mistranscribed table stays the
   right LENGTH but has wrong VALUES at some positions instead — a subtler,
   silent-wrong-output bug rather than a hang).
2. **Adversarial-probe-driven runaway allocation.** The empirical technique
   "sequentially decode container index 0, 1, 2, ... until the codec
   itself throws" (used to find a real picture count with no directory
   sentinel to read) fed genuinely out-of-range indices into the decoder.
   Reading the directory at an out-of-range index landed on unrelated
   payload bytes reinterpreted as a `u32` "decoded size" field; an
   unguarded `huffman.decode(sizeDst - 32)` then tried to allocate/loop
   across however many billions that garbage `u32` happened to be. Adding
   bounds-checked reads (`throw` past end-of-buffer) did **not** fix this
   on its own: the underlying bit-reader had a real, deliberately-preserved
   quirk from the original source — once fewer than 2 bytes remain, it
   silently stops refilling (reuses stale state) rather than throwing — so
   the bounds-checked read was never actually reached on the runaway path.

## The fix

- **Verify a hand-transcribed numeric table's length programmatically**
  against the original source (a counting script parsing the source text),
  not by re-reading it a second time — a second manual pass is a second
  independent chance to drop entries, and length is exactly the property a
  human skim won't catch.
- **Bounds-check every raw byte/word read** in the ported decoder (throw,
  don't return `undefined`) — necessary but **not sufficient** on its own.
- **Separately cap every count/size field read from the data itself**
  before it's used to drive a loop bound or `new TypedArray(n)` allocation
  — with an explicit plausibility bound derived from the format's real
  content (e.g. "every real record decodes to ~5KB, so cap at 200KB, not
  `Number.MAX_SAFE_INTEGER`"). This catches exactly the case where
  intermediate state (a stale bit-reader value, a partially-consumed
  buffer) can mask an out-of-bounds condition that a plain `buf[i]` bounds
  check would otherwise have caught.
- When adopting the "probe sequential indices until failure" technique for
  finding a real element count with no directory sentinel, budget for
  fixing exactly this class of bug — it is the single most common failure
  mode that technique surfaces, precisely because it's the first thing to
  feed the decoder genuinely adversarial input.
