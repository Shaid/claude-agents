# A familiar extension is not proof the file follows that format's real spec

**When it bites:** a file's extension matches a well-known interchange
format (`.LBM`→IFF ILBM, `.PCX`, `.BMP`, `.WAV`, `.MID`...) and a doc or
prior pass already labels it that way, but you haven't actually checked the
first bytes against that format's real magic/chunk structure — especially
when you're about to write a standard-format parser (an IFF `FORM`/chunk
walker, a RIFF reader) against it, or cite the standard format's own field
layout in a spec doc without having found a single matching magic byte.

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
all, just an absent one nobody checked for.
