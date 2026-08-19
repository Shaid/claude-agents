# A CRI `@UTF` binary table's strings are Shift-JIS, not UTF-8, on a Japanese-developed title

**When it bites:** decoding a CRI Middleware `@UTF` self-describing binary
table (the format underlying `CPK`, `ACB`, `CSB`, and other CRI containers)
and a subset of string-column values — usually filenames or cue/track
titles, not every string in the table — come out as mojibake (garbled
multi-byte sequences, replacement characters, or nonsense punctuation)
while the rest of the table (numeric columns, row counts, offsets) parses
perfectly cleanly.

Confirmed on NieR (2010, PS3, `flower` project): `tools/shared/cri-cpk.ts`'s
`UtfTable` string decoder (`cstr()`) was hardcoded to `Buffer.toString
('utf-8')`. Every ASCII path/filename in the corpus (the overwhelming
majority) decoded fine, masking the bug for two full RE passes. It only
surfaced once a **nested** CPK archive's own `Toc.FileName` column was
inspected — `AUDIO/NIER_BGM.CPK`'s real Japanese developer BGM cue titles
(e.g. a track plausibly meaning "Nier's Village: base ambient sound 01")
decoded to garbled replacement-character soup under UTF-8. Switching the
decoder to Shift-JIS (Node's built-in `TextDecoder('shift_jis')`, no extra
package — same primitive already banked in `game-re-tooling/psx.md`) fixed
it immediately, with **zero regression risk**: every plain-ASCII string
this project's other `@UTF` consumers already depend on round-trips
byte-identically under either encoding, confirmed by the full pre-existing
test suite passing unmodified after the change.

**The fix:** for a Japanese-developed title's own `@UTF`/CRI-format string
tables, default the decoder to Shift-JIS, not UTF-8 — CRI Middleware is
overwhelmingly used by Japanese studios and their own internal asset/cue
naming is routinely authored in Shift-JIS even when the shipped disc's
*other* text assets (subtitles, credits) might use a different encoding.
Don't wait for garbage bytes to notice this: ASCII-only sample rows (the
first files anyone checks, since they're the easiest to eyeball) look
completely correct under UTF-8, so the bug hides until a **non-ASCII**
string is specifically inspected — which for a CPK archive is more likely
inside a Japanese-language-only sub-container (BGM cue sheets, Japanese
voice banks) than the top-level, often English-named directory/file
listing sampled first. One known caveat where a Shift-JIS decoder still
isn't perfectly correct: Microsoft's cp932 (Windows-31J) diverges from
strict Shift-JIS on a handful of characters (notably the long vowel mark
`ー`, which strict Shift-JIS maps to the fullwidth reverse solidus `＼`
instead) — cosmetic only if Node's ICU build lacks a `cp932` decoder (it
commonly does), and irrelevant to any functional/structural decode.
