# An otherwise-clean extracted string with one odd byte may hide a periodic interleave, not corruption

**When it bites:** a decoded/extracted text field (a name, a label) reads as
almost entirely clean printable text but has one non-printable or
wrong-looking byte sitting mid-string at a position that varies between
records — tempting to write off as "one corrupted byte" or a stray control
character and move on.

Check first whether the odd byte recurs at a **fixed period** measured from
the *start of the name region*, not at a fixed absolute file offset. A
single isolated bad byte per record, at a position that differs record to
record but always lands on the same modulus, is a discarded interleaved
byte (a formatting/attribute/wrap marker), not noise — the true text is
every byte *except* the ones at that period.

Confirmed on Warriors of Legend's `scenes.res` `NECS` resources: 287/316
carry an embedded scene/location name in a trailing mostly-printable run,
but the raw bytes read like `"Th<0xFF>e Canyon<0x3F>nlands"` — one stray
byte breaking up otherwise-legible text, at a different position in nearly
every record. Brute-forcing all 9 possible phases of "drop every 9th byte
starting at phase P" and keeping whichever phase left an **all-printable**
result cleaned up 286 of the 287 (99.7%) into genuine names ("The
Canyonlands", "Moc Madure's Lair", "Mr. Bral's Stable") — the discarded
byte lands exactly every 9th position once phase-aligned. What the
discarded byte itself encodes was never confirmed (no executable trace was
available), but the **name** is confirmed by the corpus-wide clean-decode
rate, which is a strong, cheap, self-contained oracle: real names cluster
overwhelmingly in a narrow printable-ASCII alphabet, so "does removing
period-N bytes make the *whole* corpus resolve to all-printable" is a much
stronger test than eyeballing one example.

**Fix:** for a corpus of N similarly-shaped records each showing this
symptom, try every phase 0..(period-1) of a candidate period and score by
full-corpus fully-printable rate, not by fixing one example by hand. A
single high-90s%-or-better clean rate across dozens+ of records is strong
evidence the period is real; a rate near what you'd expect from chance
(a handful out of many) means look elsewhere (wrong period, or genuinely
per-record corruption). Don't skip trying a handful of small candidate
periods (a boundary near the text's own natural word-wrap width — 8, 16 —
is a good first guess) before concluding the pattern doesn't exist.
