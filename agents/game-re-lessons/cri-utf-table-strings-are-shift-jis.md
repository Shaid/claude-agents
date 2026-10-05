# A Japanese-developed title's text field decodes to mojibake OR silent garbage under an ASCII/UTF-8 assumption — always re-check as Shift-JIS

**When it bites:** a Japanese-developed title's text field decodes oddly under an ASCII/UTF-8 assumption. Either some CRI `@UTF` table strings (CPK/ACB/CSB filenames, cue titles) come out as mojibake while numeric columns parse fine, or a printable-ASCII filter (`c>=32 && c<127`) yields short, meaningless fragments that look like truncation noise rather than failure.

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

**The silent-drop variant (confirmed on Valkyrie Profile, PSX,
`valkyrie` project).** A BGM sequence header's 4-byte "cue tag" field had
been documented across two prior passes as "blank on most songs, a
truncated ASCII/Shift-JIS fragment on the rest" — the existing decode
path filtered to printable ASCII (`c>=32 && c<127`) and dropped every
other byte, so a real 4-byte value made of two Shift-JIS characters
(e.g. `93 6f 8f ea`) produced whatever single stray byte in the run
happened to be ASCII-range (`0x6f`='o'), read as meaningless noise.
Re-decoding the exact same raw bytes with `TextDecoder('shift_jis')`
instead of the ASCII filter revealed real, meaningful Japanese words
(戦闘="battle", 固定="fixed", 精神="spirit", 不安="anxiety", 登場=
"entrance"...), several repeating across multiple unrelated real song
titles — the decisive signature of a real composer/category tag, not
truncation garbage. **The general tell:** if a field decoded via an
ASCII-only filter or byte-range check yields short, semantically
meaningless single letters or fragments — not obviously wrong (no
replacement characters, no visible mojibake) — and the game has any
Japanese development provenance, re-decode the *raw* bytes as Shift-JIS
before writing the field off as unrecoverable truncation noise. An
ASCII filter is not a neutral "best effort" decode here — it silently
produces plausible-looking wrong output instead of failing loudly.
