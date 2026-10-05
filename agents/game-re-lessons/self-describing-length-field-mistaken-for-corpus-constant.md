# A self-describing per-record length field that "always equals X" in a small sample is still a real variable, not a corpus constant

**When it bites:** a container/record table's own leading length/size field
was characterized from an early, small sample as "always equals N" (and a
reader was built around a fixed N-byte stride on that basis), and a later,
larger or different population of the same format fails that stride for a
real minority of records — especially when the failures aren't garbage, just
"tableSize/fileSize isn't a clean multiple of N," and the instinct is to hunt
for a second header field or a residual-byte formula rather than to question
the fixed-stride premise itself.

Confirmed on Valkyrie Profile 2 (PS2)'s `"SEQW"` audio container
(`tools/shared/ps2-seqw-audio.ts`). An early 285-record sample of the sample
table always had record word 0 equal to 28, so the format doc and the reader
both documented/assumed "record size is a fixed 28 bytes (14 u16 words)."
A later pass covering all 184 real top-level `seq` TOC entries found 89/184
failing that assumption (`tableSize` not a multiple of 28) — and a plausible-
looking partial fix (`(tableSize - 20) / 28`, treating the residue as a
trailing sub-block) only explained 49 of the 89 failures, leaving the rest
still broken. The real structure, found by dumping the raw table bytes of
the smallest failing entries directly instead of continuing to extend the
header-field arithmetic: record word 0 isn't a corpus-wide constant at all —
it's every record's own self-describing byte length, and a real minority of
records are legitimately 48 or 52 bytes (not 28). The field had simply never
been observed taking any other value in the small first sample.

**The fix is a strict generalization, not a branch.** Walk the table by
cumulative declared size (`nextOffset = thisOffset + declaredSize`, reading
`declaredSize` fresh from each record's own word 0) instead of a fixed
stride constant. This is the same shape of mistake as
`format-field-width-unexercised-by-first-corpus.md` (a field's *width* passes
every check in a small corpus because the values never exceeded the narrower
type) but for a *stride/length* field specifically: here the field's stored
*value* itself was mistaken for a fixed layout constant, when it was always
meant to be read as data, per record. The tell that should have shortened the
search: a "recording session bookkeeping field that always reads a fixed
constant matching the reader's own hardcoded stride" is a red flag on its
own — if a field only ever needs to hold one value, formats generally don't
bother storing it at all. Before extending a partial residual-byte formula
further, always try discarding the fixed-stride premise entirely and reading
the record's own leading field as a real per-record length, walking
cumulatively.

The same mistake has a *write-side* twin: a reader that treats such a field
as an opaque "always N" constant produces a writer that invents N (or 0) for
generated records, and the engine's own parser — which reads the field as a
real count — desyncs and crashes. See
`unknown-constant-field-is-engine-grammar-load-bearing.md`.
