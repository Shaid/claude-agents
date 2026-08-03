# A variable-length string's terminator scan must be code-aware, not a raw byte pre-scan

**When it bites:** writing a "find where this null/sentinel-terminated
string ends" helper for a text format that has *any* 2-byte (or wider)
character code — before trusting a `for (i=start; bytes[i] !== 0; i++)`-style
pre-scan to bound the slice you hand to the real decoder.

A text format that mixes 1-byte and 2-byte codes (common for scripts with a
kana/kanji or DBCS split, but the same shape shows up anywhere a "wide"
code exists alongside a narrow terminator value) can have a perfectly
legitimate 2-byte code whose second byte is numerically equal to the
string terminator. A byte-level pre-scan that looks for the terminator's
raw value has no way to know it's looking at the second half of a wide
code rather than a real terminator — it will truncate the string early,
silently, with no error, right after the 2-byte code's first byte's glyph.

Confirmed on Final Fantasy V (SNES, `ceres` project): dialogue text mixes
single-byte kana codes with 2-byte kanji codes (`0x1E`/`0x1F` bank byte +
index). Kanji code `0x1E00` = "王" (a common word, "king") — its second
byte is literally `0x00`, the same value used elsewhere as the string
terminator. A test harness that pre-sliced each dialogue line by scanning
for the next raw `0x00` byte truncated every line containing that one
specific kanji glyph immediately after it — 130/2160 lines (6%) came out
truncated, all with the exact same shape (cut off right after a name/word
ending in "王"). The real decoder (`decodeText` in `tools/ffv/text.ts`)
was already correct — it consumes codes 2-byte-lookup-first and only
treats a decoded *code value* of `0` as the terminator, never a raw byte
value — the bug was entirely in the test harness's separate, cruder
pre-slice step feeding it too-short input.

**The fix generalizes:** never bound a variable-length string by scanning
raw bytes for the terminator value ahead of the real decode. Either (a) run
the decode loop directly against a generously-oversized window and let it
find its own true end by tracking consumed-code semantics (the same logic
that would correctly consume a matched 2-byte code before checking the next
position), or (b) if a separate length-finding pass is unavoidable (e.g. to
report consumed-byte counts), make that pass code-aware too — it must know
which byte positions are valid code starts and skip the second byte of any
matched wide code, exactly like the real decoder does. A pre-scan that only
knows "one specific value marks the end" and nothing about the format's
code-width rules will eventually collide with a legitimate wide code whose
tail byte matches that value.
