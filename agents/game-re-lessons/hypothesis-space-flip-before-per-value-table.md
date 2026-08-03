# Before building a per-value lookup table from a byte diff, test whether one global rule fits every value at once

**When it bites:** a byte-diff against a small/sparse oracle (few examples
per distinct type/id/opcode value) suggests a transform's boundaries or
parameters *depend on* that value — you're about to build a per-value
table, or plan expensive per-value tracing (disassembly, code xrefs) to
fill in values the oracle doesn't cover.

A per-value framing that "sort of fits" the data you have is exactly the
symptom of testing hypotheses one value at a time against a small sample,
rather than testing whether a *single* rule explains every value at once.
Low-n examples (especially with palindromic/zero byte pairs) can't
disambiguate "this pair swaps" from "this pair doesn't swap" — both
readings satisfy a value with too few or too trivial examples — so a
per-value test silently accepts spurious "boundaries" that a holistic test
would immediately reject as inconsistent with the other 38 values.

**The fix: flip the hypothesis space.** Instead of asking "what
transform fits value X", enumerate the (usually small) space of *candidate
global transforms* and ask "which one is consistent with every value
simultaneously, using every available example of every value as one pooled
constraint set." If the parameter space is small (partitions of N bytes
into runs of size 1/2, a handful of bit-widths, a few endianness/order
options), brute-forcing all candidates against the pooled evidence is
cheap and decisive — a single candidate consistent with all values, and
uniquely so for the values with enough instances to pin it down, is far
stronger evidence than N separate per-value fits from small samples.

Confirmed on Black Crypt's DOS demo `maindung.gam` converter
(`~/Development/crawl`): a 20-byte item/monster/structure record's
Amiga→DOS byte-swap was initially framed as "boundaries depend on the
record's itemType byte" from a 225-mismatch diff on map 1, with 9 of 48
itemType values having zero instances there (implying 9 separate
crypt.exe disassembly traces to resolve). Testing every partition of the
itemType-specific 13-byte span into 1-byte/2-byte runs (377 candidates)
against every map-1 example of *every* type at once found one composition
consistent with **all 39 observed types, zero exceptions**, and unique for
the 5 types with enough instances (n=3 to n=16) to fully disambiguate it.
The rule turned out itemType-*independent* — a mechanical porting tool
re-encoded record shape, not record meaning — collapsing 9 planned code
traces into a two-line structural argument, with the *real* (small,
clean) variance turning out to be a completely different bit (monster
marker) that the itemType framing had been masking. See
`docs/blackcrypt/dos/data-structure.md` § "Record byte-swap is not a
blanket word-swap" in that project for the full worked example.

**General shape to watch for:** any "field/boundary/parameter depends on
`<discriminator>`" claim built from a diff where most discriminator values
have only 1-3 examples — before accepting it (or budgeting per-value
tracing to fill gaps), check whether a single value-independent rule
already explains the full pooled dataset.
