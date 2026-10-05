# A doc's "which of these N duplicate sub-structures?" may be immaterial — test that before answering it, and check the fields your parser reads past

**When it bites:** project docs (or a community template's own comment) flag
a choice among several same-typed sub-structures as undecided — "a block can
carry more than one `SM1G`/palette/header; which one the data resolves
against is undetermined upstream" — and the code picks one by a heuristic
("most bones", "largest", "first"). Especially when a task brief hands you
that ambiguity as the presumed root cause of a real bug.

## What went wrong

A `re-codebreaker` escalation was briefed with exactly this premise: G1M
blocks carry up to three `SM1G` skeleton subsections, the exporter picked
"most bones" as a heuristic, and a visible cloth-rendering bug was assumed to
follow from picking wrong. Two measurements dissolved the question before any
selection rule was designed:

1. **The alternatives were not distinguishable.** Scored against an
   independent per-entry invariant, *every* `SM1G` copy in a block gave a
   byte-identical result in all **362** multi-`SM1G` models in the corpus
   (232 were numerically identical rigs outright; the other 130 differed only
   in bones no binding referenced). No selection rule could be wrong, so the
   ambiguity could not be causing anything. The real bug was elsewhere
   entirely — a different field being used as the joint index.

2. **Where the copies genuinely did differ** — sibling blocks inside one pack
   in the two sibling games — the answer was already in the file and already
   being parsed past. `SM1G`'s header carries `usesInternalBoneset`, `1` on
   the real 200+ bone rig and `0` on every 1-to-10-bone geometry-block stub.
   The parser read the field's offset to reach the next one and discarded the
   value. Reading it turned the heuristic into a rule in one line.

## The two checks, in order

- **Is the choice observable?** Run whatever oracle you have under *each*
  candidate and compare. If they score identically corpus-wide, say so and
  move on — an "undetermined" that cannot change any output is documentation
  debt, not an open question, and chasing it will not fix a bug it cannot
  cause. This is also the honest thing to write in the docs: "immaterial,
  measured across N files", not "resolved by picking X".
- **Does a skipped field already answer it?** Diff your struct reader against
  the format's full declared field list and look at every field you compute
  an offset from but never store — flags, counts, "reserved", version bytes.
  A discriminator between near-duplicate sub-structures is very often sitting
  in one of them, because the engine needs to make the same choice at
  runtime and has no other place to record it.

Corollary for briefs: an inherited "undetermined upstream" is a premise to
audit, not a given. Community templates mark things undetermined because the
template author did not need them, which is weak evidence about the format
and none at all about your corpus. Related:
`stale-compressed-verdict-relocate-real-header.md`,
`community-template-field-order-wrong-not-just-width.md`.
