# "I searched and found nothing" is a weak negative; "I enumerated every access root" is a strong one

**When it bites:** you're about to write up "no code reads this field / no
consumer exists / this item has no effect", and the evidence is that one or more
searches returned zero hits.

There are two fundamentally different ways to build a negative, and they have
very different reliability:

- **Shape-based:** enumerate instruction/operand patterns that *would* access
  the thing, search for each, find none. This is only ever as complete as your
  enumeration of shapes. Every encoding you didn't think of is a silent hole,
  and you cannot tell from the result whether the hole exists. It fails
  *quietly* and produces confident wrong answers.
- **Root-based:** enumerate every way an address for the thing can be *formed*
  in the first place, then follow each root forward to a finite, classified set
  of accesses. This is countable. If the roots are complete, the access set is
  complete, and a negative over it is real.

For SAS/C small-data 68k the root chain is:

1. No absolute relocations point into the table (check the hunk's reloc block) —
   so nothing reaches it by absolute address.
2. Enumerate every `(d16,A4)` displacement that resolves into the table's byte
   range — a complete, finite root set, because A4 is the only base.
3. Pointer-escape analysis: show the derived pointers never leave their stack
   frame (no store to a global, no pass to a function that retains it).
4. What remains is a finite, individually classified set of access instructions.

Worked contrast, both from War in Middle Earth (`middilgard` project):

- **Strong.** "Are there character-death game-end conditions?" A raw scan of the
  entire CODE hunk for the two ending-stub displacements returned **exactly two
  hits each** — so the binary has exactly four game-end trigger sites, all four
  decoded, none reading a character death. The conclusion doesn't rest on a
  pattern search at all: a death ending cannot exist because there is nowhere
  for it to dispatch to. That negative is airtight by construction.
- **Weak, and it broke.** "Does the Elven cloak do anything?" A census
  enumerating operand shapes around the item field returned nothing, and was
  written up as "confirmed inert". It was wrong — the real test used an operand
  shape the census never covered (see
  `bitfield-spans-multiple-addressable-bytes.md`). The sibling coil-of-rope
  negative, reached the same way, then had to be re-argued from the addressing
  root before it could be trusted — and this time it held.

**Fix:** when a negative is load-bearing — it closes a question, contradicts
prior documentation, or lets you stop looking — do not ship it shape-based.
Convert it to root-based, or state plainly in the docs that it is a search that
came up empty rather than a proof of absence. Those are different claims and
should never be written as the same one.
