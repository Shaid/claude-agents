# A confirmed field width — or hardcoded constant-selection branch — can be unfalsified, not verified, if the first corpus never exercises its full range

**When it bites:** reusing an already-"confirmed" decoder (byte-exact on its
original game/corpus, zero errors) against a sibling game on the same engine,
platform-wide format, or container format, especially when the sibling's
files/resources run noticeably larger than anything the original corpus
contained, **or** ships a header/version field whose one observed value
in the first corpus was silently treated as the only possible value. Also
bites when a **vendored third-party reference tool** (not your own code)
outright refuses to open a structurally valid file from a game/title
outside the small corpus its own authors tested against — its format-
recognition gate can be just as overfit as a hand-written decoder's.

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

**A third instance, and a variant worth calling out explicitly: the
"decoder" doesn't have to be your own code — a vendored, trusted
third-party reference tool's own format-recognition *gate* can be just as
overfit.** Confirmed on NieR (2010, Xbox 360) in `~/Development/flower`
(`docs/nier/x360/data-structure.md` §3.4). vgmstream's real, working CRI
AIX parser (`meta/aix.c`, already vendored in this project for a sibling
game) hard-rejects a structurally valid AIX file with
`if (read_u32be(0x0c,sf) != 0x00000800) goto fail;` — a field the source
code itself only guesses is "header size?" (comment includes the question
mark). Every AIX sample the vgmstream authors tested against (SoulCalibur
IV, Dragon Ball Z: Burst Limit, per the source's own citation comment)
apparently produced exactly `0x800` there, so the hardcoded equality check
"passed every available check" the same way a narrow field width does —
except here the corpus that never falsified it wasn't the RE session's
own, it was upstream's. NieR's own AIX files carry a *different, real*
value at that offset that varies per file (not evidence of a bad
extraction — the segment/layer table immediately following it parses to
byte-exact-correct sample counts/rates/durations regardless), so vgmstream
refuses to open the file at all (`failed opening ...`) rather than
producing garbage — a *louder* failure than the silent-garbage cases
above, but the same root cause: a value/constant that happened to be
constant across the *tool's own* narrow validation corpus, encoded as if
it were universal. Confirmed real by patching just that one 4-byte field
to vgmstream's expected constant in a scratch copy (no other bytes
touched) and getting a clean, correct 6-channel/48kHz PCM decode out the
other side — proof the rest of the container's real structure was already
correctly understood, only the gate was wrong.

**A fourth instance: a community binary template scoped to "the common case"
by its own header comment, with no validation gate at all — so an untested
codec branch doesn't error, it silently decodes to internally-inconsistent
garbage.** Confirmed on Fire Emblem Warriors (2017, Switch, `chimera`
project, `docs/fe-warriors.md` "Audio"). The public `three-houses-research-
team` `KTSS.bt` 010 Editor template (already trusted as the reference for
this same project's Three Houses/Three Hopes audio, both `codecID=9`)
states its own purpose as "Parsing KTSS (music and voices) **OPUS** files"
and declares one fixed field layout with no `codecID`-dependent branching
— unlike instance 3's vendored tool, it has no gate to refuse anything.
Applying that fixed layout to FE Warriors' `codecID=2` streams (a corpus-
wide census found *every* KTSS block in the game uses `codecID=2`, zero
exceptions) "parsed" with no error — no bounds check tripped, no magic
mismatch — yet was provably nonsense: the `audioOffset` field read back
byte-identical to the already-parsed `sampleCount` field, and
`packetCount=1` for a track with 3.5 million samples/channel. Consulting
`vgmstream`'s independent implementation (`src/meta/ktss.c`) showed
`codecID=2` is GameCube/Wii DSP-ADPCM with a completely different,
version-dependent layout past byte 0x20 (its source comment even names
this exact game: `/* DSP ADPCM - Hyrule Warriors, Fire Emblem Warriors */`)
— the template was never wrong about `codecID=9`, it simply never claimed
to cover anything else. **The tell wasn't a crash — it was a duplicate/
self-referential value only visible by cross-checking two already-parsed
fields against each other**, not any single field looking implausible
alone.

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

**When you *do* find the sibling's changed constant, prove the old one fails
across 100% of the new corpus — don't stop at "the new one works."** A layout
constant that genuinely moved between ports is easy to confirm sloppily: the
new value parses cleanly, you write it down, done. But "the new value works"
is also true of a value that merely works *better*, and it leaves open whether
you found the real constant or a lucky one. Running both is one extra loop and
turns a plausible fix into a two-sided result. Confirmed on Phantasie I
(Amiga) vs. Phantasie II (Atari ST) in the `nicodemus` project: the two ports
share this world-map format's reader code *instruction for instruction* —
identical grid math, identical 5-byte POI record stride (including the same
latent over-read past the table's declared end), identical 3-arm
message-length encoding, identical fog-of-war flag, identical section-mosaic
arithmetic — and yet the per-section icon display list sits at offset 1000 in
one and 1500 in the other, inside a record that grew 2500 → 3000 bytes.
Parsing the P2 corpus at 1500 succeeded **17/17**; parsing the same files at
P1's 1000 failed **17/17**. The clean split across the whole corpus in both
directions is what makes it a fact rather than a working value — and note the
broader warning it carries: "same engine, same code, byte-identical readers"
does not imply "same layout constants", so a shared-engine finding licenses
reusing the *structure*, never the *offsets*, without re-deriving them.
