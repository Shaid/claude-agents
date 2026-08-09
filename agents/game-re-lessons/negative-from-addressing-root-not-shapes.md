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
- **Weak by construction, not just by omission.** Carrier Command (Amiga): a
  literal-address `BSR`/`JSR $TARGET` byte-pattern scan is inherently
  shape-based — it can only ever match a *direct* call encoding. A candidate
  routine (`$CB5C`) had 12 confirmed direct callers, none of them the one call
  site in question (`$B742`'s model loader) — read as disqualifying evidence
  and the routine was "ruled out" as that call's target. But `$B742` calls its
  target via `JSR (A2)`, a **register-indirect** call with `A2` loaded from
  data at runtime (`MOVEA.L (A0)+,A2` immediately before the `JSR`). No literal
  target address exists in that instruction at all — a scan for `BSR`/`JSR
  $CB5C` is *structurally incapable* of ever matching it, no matter how
  exhaustive. The 12-caller census was true and complete for direct calls, and
  said nothing whatsoever about the one indirect call that mattered; "ruled
  out" had to be walked back to "undecided." The root-based fix here is to
  enumerate where the *register* (`A2`) gets its value — trace every write to
  it, including ones sourced from data/memory, not just literal-immediate
  `LEA`/`MOVEA.L #imm`. A pure byte-pattern scan for `JSR $addr` forms cannot
  do this; it needs either a data-flow trace back from the `JSR (An)` site, or
  a live capture of the register at the call.

**Fix:** when a negative is load-bearing — it closes a question, contradicts
prior documentation, or lets you stop looking — do not ship it shape-based.
Convert it to root-based, or state plainly in the docs that it is a search that
came up empty rather than a proof of absence. Those are different claims and
should never be written as the same one.

**A root-based census can still be incomplete if it only greps the array's
*unindexed* base constant, missing every literal-index access compiled to a
different constant.** War in Middle Earth (`middilgard`): a shared,
FRML-id-indexed pointer array lives at base `SECSTRT_0-10674(A4)`, written
once per id as `arr[id] := handle` (`base + 4×id`). A census concluded "only
one routine in the whole binary references this array" by grepping for the
literal string `10674` — genuinely root-based in spirit (searching for the
array's own address, not an instruction shape), but incomplete, because
every *other* consumer that indexes the array with a **literal** id has that
arithmetic folded by the assembler into its own distinct constant
(`-10674 + 4×id`, e.g. `-10650` for id 6, `-10642` for id 8) with no
occurrence of `10674` anywhere in the instruction. The true second consumer
(four such accesses, for four different literal ids) was invisible to the
one-string grep and the negative was wrong. **Fix:** once a base and stride
are known, the addressing-root enumeration is not complete until you also
compute and search for `base ± stride×n` for every plausible index `n` in
the domain (here, the small set of known valid ids) — not just the bare base
string. This is the same "enumerate every root" discipline as the `(d16,A4)`
displacement method above, just applied one level deeper: the "root" for an
array is not one constant, it's a *family* of constants parameterized by
index, and a grep for only the family's zero-offset member is shape-based
in disguise.

**A negative can also be an artifact of the search *tool*, not just its
shape — re-run a load-bearing zero-hit result with an independent, simpler
method before trusting it.** Hunter (Amiga, `hunter` project): a prior
session documented "no code in `game_decrypted.bin` reads back the OB-format
header's `+0xc` longword" as a confirmed negative, evidenced by `r2 /x`
byte-pattern searches for the field's cached scratch-memory displacement
finding nothing beyond the one known write. A later session re-ran the
identical question with a plain Python `bytes.find()` over the raw file and
found a real second hit immediately — a genuine consumer routine
(`move.l 0x157c(a5),d6 ; beq ; bsr`) that the disassembler's own search
feature had somehow missed, root cause not identified (search-scope option,
an indexing gap, or an operator error in the invocation — moot; the
disassembler's search is not infallible). The fix isn't "root-based vs.
shape-based" here — the search *was* root-based (searching for the one
displacement value at the addressing root, not enumerable instruction
shapes) — it's that even a well-designed search is only as trustworthy as
the tool executing it. Before writing up a load-bearing "confirmed inert,
zero consumers" from a single tool's zero-hit result, re-run the identical
byte-level question with a second, independent, dumber method (a raw
`bytes.find()`/`grep -a` over the file beats trusting one disassembler's
search implementation) — it's minutes of work and it overturned a
"confirmed" verdict a prior session had closed with a full closure
argument.

**The same "structurally cannot exist" root cause applies to *content*
searches, not just consumer searches — and a noted-but-unexplained anomaly
can be the resolving fact, not a distraction from it.** Phantasie III
(Amiga, `nicodemus` project): two local attempts to find the file location
of several `HUNK_RELOC32`-resolved lookup-table addresses both failed
(a literal base-offset guess, and a brute-force monotonic-value scan) —
both were, without realizing it, searching for file bytes that don't
exist, because the target hunk's `HUNK_DATA` block stored fewer bytes than
its `HUNK_HEADER`-declared allocation (a SAS/C merged `data+bss` hunk; see
`hunk-data-shorter-than-declared-is-merged-bss.md`). The escalation brief
that finally cracked it had flagged the size mismatch as a peripheral
"worth double-checking" anomaly alongside the real question ("what base do
I add") — the fix was recognizing the anomaly *was* the answer (no base
exists; the references are runtime BSS variables, not stored content), not
a side detail to verify away before returning to the main search.
