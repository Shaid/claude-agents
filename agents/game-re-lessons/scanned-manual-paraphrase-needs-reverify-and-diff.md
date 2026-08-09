# A scanned first-party manual is a strong oracle, but only the page images — not a prior paraphrase of them — and only after an exact diff, not an eyeballed one

**When it bites:** a task hands off a paraphrase/transcription of a scanned,
text-layer-less manual/rule book (numbers, names, category boundaries) as
if it were already-verified ground truth, and you're about to decode
something against it, or report a "byte-exact, zero deviations" match
against it without having run an actual programmatic diff.

A first-party, contemporary manual (a real SSI/whoever rule book, scanned
to PDF with no text layer) is a stronger oracle than any third-party
fan-tool reimplementation — but two distinct failure modes sit between
"a manual exists" and "the match is real," both confirmed in the same
session (Phantasie III, Amiga, `nicodemus`):

**1. A paraphrase of scanned page images can itself contain an eyeballed-OCR
slip, even when written carefully and with an explicit warning attached.**
A task's own transcription of an item catalogue listed `"Halbred"`; the
actual manual page image (re-read directly via `Read`'s `pages` parameter)
prints `"Halberd"`, matching the game's real data exactly — a letter
transposition introduced somewhere in the human-or-agent transcription
step, not a real manual/game discrepancy. Any paraphrase of a scanned
image — including one handed to you as if already fact-checked, and
including one you wrote yourself in an earlier turn — needs a re-read of
the actual page image before it's used to make a confirmed/refuted call,
not just before it's used for the first time. `Read`'s `pages` parameter
(max ~20 pages per call) makes this cheap enough to do routinely for any
specific claim that matters.

**2. Do the diff programmatically and report the true count — a partial
match is not "byte-exact, zero deviations."** Diffing the same catalogue
(120 items, re-verified against the real manual images) against the
game's own already-extracted item-name string table found **117/120
exact, not 120/120**: two matches were cosmetic spelling only (`"God
Armour"` vs. manual `"God Armor"`), but one pair was a real, non-cosmetic
content divergence — the manual's own printed catalogue says `"Knife
+1"`/`"Knife +2"` at item indices 81/82, while the shipped Amiga binary's
data says `"Dagger +1"`/`"Dagger +2"` at the identical indices (verified
independently on both sides: the manual page re-read fresh, the game
bytes re-extracted fresh). Every other `+N` pair in the same range matched
exactly, ruling out a systematic offset — this is an isolated two-entry
divergence, plausibly a late rename or a genuine manual erratum, and it's
real regardless of cause. The fix: run the actual name-for-name diff in
code and report the exact mismatch count and which specific entries
differ, rather than skimming a long list and concluding "looks like a
match" — a 97.5% match rounds up to "confirmed" far too easily if nobody
counts, and the two-entry divergence would have been silently lost.

**When the manual and the game data disagree, the game's own bytes are
authoritative for extractors/assets** — the manual is a cross-check
oracle for catching bad decodes and confirming ambiguous readings, not a
data source to override real bytes with. Document the divergence
explicitly rather than picking a side silently.
