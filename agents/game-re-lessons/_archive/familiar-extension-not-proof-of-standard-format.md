# A familiar extension is not proof the file follows that format — or category — its name implies

**When it bites:** a file's extension matches a well-known interchange
format (`.LBM`→IFF ILBM, `.PCX`, `.BMP`, `.WAV`, `.MID`...) — or just
strongly suggests a content *category* via project-internal or genre
convention (e.g. `.TIM` "smells like" a texture because a sibling `TIM2`
format exists elsewhere in the same corpus) — and a doc or prior pass
already labels it that way, but you haven't actually checked the first
bytes against that format's real magic/chunk structure. Especially risky
when you're about to write a standard-format parser (an IFF `FORM`/chunk
walker, a RIFF reader) against it, reach for an existing sibling decoder as
a "probably the same, different magic" candidate, or cite the assumed
format/category in a spec doc without having found a single matching magic
byte. **A distinct, sharper failure mode of the same root cause: the
extension doesn't just mismatch a format, it actively suggests the WRONG
CONTENT CATEGORY** — enough that a naive per-extension pipeline dispatcher
would *exclude* the file from processing entirely (not just misdecode it),
because the extension reads as "not this kind of asset at all." This is
worse than a wrong-format label, since a wrong format at least gets
attempted and fails visibly — a wrong-category extension can make a file
silently never reach any decoder.

Confirmed on NieR (2010, PS3, `flower` project): a `.TIM` extension
strongly suggested a texture (this project's own `.TIM`/`TIM2` prior art
elsewhere made that a reasonable first guess, and even prompted checking
the project's existing TIM2 decoder as a candidate reference), but the real
decompressed bytes carried an unrelated magic (`MTMI`) and structure
entirely — a flat, fixed-stride table of attack/motion animation-clip
names, verified byte-exact via `recordCount * strideBytes + headerBytes ==
fileSize` holding on 6/6 real samples, zero pixel/palette data anywhere in
it. The check that caught it was the same one-line discipline as the
standard-format case below: read real bytes before trusting the name.

Confirmed on Epic (Ocean, Amiga, 1992): every `.LBM` file's decompressed
content had been carried in the project's docs as "IFF ILBM" purely on the
strength of the extension — a completely reasonable-looking assumption,
since Amiga games from this era genuinely do ship IFF ILBM screens
constantly. Writing an actual `FORM`/`ILBM`/`BMHD`/`CMAP` chunk parser
against the real decompressed bytes found **zero** matches: no `FORM` tag
anywhere in any of the ~20 `.LBM` files. The real content: `word[0] = 0`,
followed by 15-31 more words that are all valid 12-bit Amiga RGB4 values
(`<= 0x0FFF`), then raw bitmap data — a custom `[16- or 32-entry
palette][pixels]` layout invented by this specific game's tooling, sharing
nothing with IFF beyond "it's a palette followed by pixels" and the
coincidental `.LBM` extension (itself just Deluxe Paint's generic save
extension, not a format guarantee). The confusion was cheap to have and
would have been near-invisible without directly probing the bytes — a
palette-shaped word run at offset 0 looks exactly as "correct" whether it's
preceded by a `FORM` header or not, so a decode that just skips to "palette
starts around here" can silently succeed on the wrong premise for a long
time.

Confirmed on Reunion (Amnesty Design, Amiga AGA, `methanoid` project): a
`.BAT` extension inside `sound/` — an extension that on any other platform
reads as "an MS-DOS batch script, not a game asset" — decompresses (via the
corpus's shared IMP!/File-Imploder unwrap) to a genuine IFF `8SVX` audio
sample, byte-identical in structure to every properly-named `.SND`/`.EFX`
sibling in the same directory. A `.RDA` extension likewise looked
ILBM-shaped by directory co-location with `.CHR` files, but decoded as
chunky `PBM `, not planar `ILBM` — same IFF family, wrong sub-format, still
caught only by reading real chunk tags. The fix that generalizes from this:
dispatch every file in a mixed corpus on its own **decompressed magic
bytes**, never on its extension, in either direction (neither "this
extension means skip it" nor "this extension means format X") — one
extension-agnostic classifier pass over real bytes is cheap and closes both
failure modes at once.

Confirmed on Eye of the Beholder II (Amiga, `crawl` project): `TEXT.CPS`,
`TEXT2.CPS`, and `TEXT4.CPS` carry the exact same `.CPS` extension as over
100 real bitmap files in the same corpus (every one of which really is an
LCW-compressed Amiga bitmap) — but these three are not images at all. No
`TEXT.DAT` file exists anywhere in this corpus; the game's dialogue-text
table was simply shipped through the same generic "LCW behind the shared
Kyra bitmap header" container every `.CPS`/`.VCN`/`.INF` in the corpus
uses, for a payload type with zero pixel/palette content. Caught by
decoding, not guessing: LCW-decompressing any of the three yields exactly
22,463 bytes — byte-for-byte the sibling DOS port's own real `TEXT.DAT`
file size — and that payload parses cleanly as the same offset-table +
NUL-terminated-string-pool format already confirmed for DOS, with the
decompressed bytes **md5-identical** to DOS's real `TEXT.DAT` in all three
files. This is the same trap as the `.LBM`/`.TIM`/`.BAT` cases above, one
level up: not just "the wrong sub-format under a shared magic," but "an
unrelated *content category* riding a whole other format's container and
extension convention" — worth checking even when the extension is locally
well-attested by dozens of genuine same-extension siblings in the same
corpus.

**The fix:** before parsing a file as a named standard format, or before
writing that name into a spec doc as more than a first guess, read the
first 4-12 bytes and check them against the format's real magic (`FORM....
ILBM` for IFF, `RIFF....WAVE` for RIFF/WAV, `\x0A` + version byte for PCX,
`BM` for BMP, etc.) — this is a one-line check, cheap enough to do before
committing to the assumption in any doc or extractor. A mismatch doesn't
mean "this game corrupted the format" — it usually means the extension is
just a convention the game's own tooling chose (often because the original
authoring tool, like Deluxe Paint, defaults to it), not a guarantee about
the byte layout. This pairs with, but is distinct from,
`renamed-magic-container.md` (a *compression* container with its magic
bytes deliberately swapped) — this trap has no renamed magic to spot at
all, just an absent one nobody checked for. A sibling failure mode one
level down, for formats with no filename/extension at all: a numeric
discriminant *field* (not a filename) that happens to match a well-known
SDK enum's own numbering for one observed value — see
`pixel-format-value-guessed-from-enum-not-confirmed.md`.
