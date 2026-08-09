# A confirmed field width — or hardcoded constant-selection branch — can be unfalsified, not verified, if the first corpus never exercises its full range

**When it bites:** reusing an already-"confirmed" decoder (byte-exact on its
original game/corpus, zero errors) against a sibling game on the same engine,
platform-wide format, or container format, especially when the sibling's
files/resources run noticeably larger than anything the original corpus
contained, **or** ships a header/version field whose one observed value
in the first corpus was silently treated as the only possible value.

A numeric field's width (u16 vs u32, i8 vs i16, ...) can pass every
available check on the game it was derived from — a full corpus scan with
zero decode errors, clean renders, byte-exact structural invariants — while
still being wrong, if every real value in that corpus happens to fit inside
the *narrower* width being (incorrectly) read. The narrower read and the
correct wider read are bit-identical whenever the high bits are all zero,
so nothing in the first game's data can ever expose the mistake; "confirmed
against every file in the corpus" quietly means "confirmed against every
file whose true values stayed under 2^16," not "confirmed as a field-width
fact."

Confirmed on Dungeon Hack (`~/Development/crawl`, AESOP/16 engine, shared
with Eye of the Beholder III): `eotb3lib/bitmap.py`'s "old format" bitmap
sub-image offset table was read as `u16` per 4-byte table slot (only the
low 2 bytes of each slot), verified byte-exact and zero-error across EOB3's
entire `EYE.RES`/GFF corpus for over a full RE pass. EOB3 never has a
resource bigger than 64 KB using this format, so the table's top 16 bits
always read `0` there — the bug was mathematically invisible. Dungeon
Hack's `"Drawbridge"` resource (130,544 B, 6 sub-frames) needs table
offsets past 65,535 for its later frames; decoding it with the old `u16`
read produced nonsense dimensions (`1544×1285`, `56025×1499`) instead of an
error, because the read is *structurally* well-formed at every width — it's
a garbage *value*, not a crash, so nothing about the failure mode
self-flags as "you're reading the wrong width." Widening the read to `u32`
fixed Dungeon Hack immediately and was verified to be a byte-exact no-op
against the *entire* pre-existing EOB3 asset output (every file, pixel-for-
pixel identical) — proof the original corpus's small values had been
masking the bug the whole time, not that the fix changed anything for that
game.

**A second instance, same root cause, different concrete shape: a hardcoded
constant-selection branch instead of a field width.** Confirmed on
`~/Development/flower`'s PS3 NPDRM `.EDAT`/`.SDAT` decryption
(`tools/shared/ps3-edat.ts`). RPCS3's real `unedat.cpp` selects between two
different fixed AES key constants for the "encrypted ERK" unwrap step via
`(NPD.version == 4) ? EDAT_KEY_1 : EDAT_KEY_0` — every other `NPD.version`
value uses `EDAT_KEY_0`. This project's decoder, built and byte-exact-
verified against Drakengard 3's entire `.EDAT`/DLC corpus, hardcoded
`EDAT_KEY_1` unconditionally and threw on any `NPD.version !== 4` — which
passed every available check (every real Drakengard 3 file genuinely is
version 4) while quietly encoding "the only version I've ever seen" as if
it were "the only version there is." The moment a sibling PS3 title in the
same project (NieR, 2010) needed to decrypt its own `STABLE.SDAT`
(`NPD.version === 2`) and DLC `.EDAT` (`NPD.version === 3`), the hardcoded
`EDAT_KEY_1` produced uniform high-entropy garbage instead of an error —
structurally well-formed ciphertext-shaped output at every step, so nothing
about the failure self-flagged as "wrong key constant" until the garbage
was diagnosed against an independent magic-byte oracle (a real `ICON0.PNG`
entry inside the decrypted content, byte-exact PNG signature only once
`EDAT_KEY_0` was used). Fixed by deriving the real
`npd.version === 4 ? EDAT_KEY_1 : EDAT_KEY_0` selector from RPCS3's own
source rather than the single value the first game's corpus happened to
exercise; Drakengard 3's own byte-exact behavior was unaffected (regression-
tested) since it only ever hits the `version === 4` branch.

The general move: when a "confirmed" decoder from one game is about to be
reused unmodified against a same-engine or same-platform-format sibling,
treat any field whose narrow-width reading happens to coincide with a
wider-width reading (i.e. any field where the observed values in the first
corpus never approached the narrower type's max) — **and any hardcoded
constant/branch choice whose selector field only ever took one value in the
first corpus** — as *unfalsified*, not *verified*. Re-derive or
independently corroborate it (a second oracle, a community tool's or public
reference implementation's own source, a structural invariant that only
holds at the correct width/constant) rather than trusting the first game's
clean track record alone. This is a sibling problem to
`fixed-stride-record-count-unverified.md` (a count formula untested past
the first row) and `record-stride-guess-vs-recount-fields.md` (a stride
guessed rather than recounted) — same root cause (a range-limited first
corpus can't distinguish "correct" from "coincidentally correct so far"),
different concrete failure shape.
