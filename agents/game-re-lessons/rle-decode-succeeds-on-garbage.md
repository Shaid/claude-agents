# A run-length decode completing without error is not verification

**When it bites:** you've decoded a candidate compressed stream (ByteRun1/PackBits, RLE, similar), it ran to completion with no bounds overrun, and you're about to call the format identified.

Simple byte-oriented RLE/PackBits schemes rarely throw on arbitrary input —
almost any byte stream can be mechanically walked as "control byte, then
literal run or repeat run" without ever reading past the buffer end, so
"it decoded without error" carries very little evidence either way.
Jungle Strike AGA: running the same ByteRun1 decoder against `panel` and
`slides` (files with no format marker, not confirmed ByteRun1) completed
cleanly with zero bounds errors, but produced non-round output lengths
(26,859 and 65,101 bytes — not a clean multiple of any plausible
bytes-per-row * plane-count). Meanwhile the real `JUNK`-tagged screens
(`brief`, `menubgd`, `menubgd2`, `status`) all decoded to an exact multiple
of 200 (40 bytes/row * 5 planes) with **zero remainder**, across all 4
files.

The actual oracle is landing on a **round, structurally-plausible output
size** (an exact multiple of a real geometry, ideally holding across
several sibling files with zero deviation), not merely "the decode didn't
crash." Absence of a bounds error is a necessary but nowhere near
sufficient condition — treat a decode that "succeeds" into a non-round size
as a rejected hypothesis, not an inconclusive one.

A size that *does* look plausible is just as dangerous if it's the only
check run: Conan the Cimmerian (Amiga) — the `Game`/`Conan` executables'
compressed DATA hunk was assumed to be Apple PackBits and decompressed with
the project's generic `packBitsDecompress`, which ran to completion with no
error at a round-enough-looking 148,002 bytes (same order of magnitude as
the target BSS reserve). That number was then treated as ground truth and
searched exhaustively (multiple palette formats, full-blob scans) for
weeks of investigative effort with nothing found — because the real
on-disk compression is a completely different algorithm (a custom
backwards-reading LZ77 engine embedded in the executable's own CODE hunk,
confirmed by disassembling that hunk directly), and `packBitsDecompress`
had simply walked the wrong bitstream to a coincidentally plausible length.
Nothing about the "successful" decode ever signaled the mistake — the tell
only showed up one level further downstream, when disassembling *that*
output found no recognisable code or data structure. When a decompressor is
embedded in the game's own executable (as opposed to a well-known standard
codec), disassemble it and confirm the algorithm family *before* trusting
any decoded output as a search target, even one with a plausible size.
