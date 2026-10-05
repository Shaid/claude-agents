# A table's element count lives in the code's own index bound check — read it per module, don't inherit a constant documented from one sample

**When it bites:** a prior pass documented a compiled structure's element
count as a fixed number ("every module's dispatch table is 9 words"), you
build a loader around that constant, and it works on most of the corpus while
a stubborn minority refuses to parse — especially when the code that uses the
table validates the index first (`slti`/`sltiu`/`cmp`+branch) before indexing
it.

## What happened

Valkyrie Profile (PSX, `valkyrie`), 655 per-unit behaviour modules. The
research doc had characterized the entry-point dispatch table from disassembled
samples as **9 words**, noting only in passing that "some modules use 10". A
loader built on 9 (with the table's contents validated) classified 590/655 and
left 65 unexplained — and those 65 were not corrupt, they just didn't have 9
valid slots at any candidate address.

They weren't a different format. 57 enemy modules bound their table with
`slti $v0,$a2,5` and carried a **5-word** table which they `jalr`'d immediately
instead of installing; another family used 4. Reading the count from each
module's own bound instruction instead of the documented constant took
classification from 590 to 641, and the remaining 14 turned out to be two
genuinely different entry shapes (a real finding that the wrong-constant noise
had been hiding).

## Why the constant is unreliable and the instruction isn't

A count documented from disassembly is a count observed in however many
samples that pass happened to read — the same failure mode as
`self-describing-length-field-mistaken-for-corpus-constant.md`, except here
the count isn't stored in a data field at all, so there's no field to notice
was varying. Compiler output, though, *must* range-check before an indexed
jump or call, so the bound is sitting right there in the prologue as an
immediate. It is per-module, exact, and free to read.

## The fix

When locating a table in compiled code, derive its length from the nearest
index-bound compare in the same function (`slti`/`sltiu` against a small
immediate) rather than a documented constant, and fall back to the documented
value only when no bound is found. Two riders:

- **The bound is an upper limit, not always the allocation.** One module
  bounded at 5 but only ever copied 4 words to the stack; validate the leading
  run of plausible entries and cap it at the bound, rather than demanding
  exactly `bound` valid entries.
- **Treat a stubborn unexplained minority as signal.** The instinct to write
  off "65 modules our heuristic misses" as a heuristic gap is what kept the
  wrong constant alive; fixing it shrank the residue to 14, of which 12 were
  a second and third real entry shape and only 2 were a true anomaly.
