# An unchanged crash after a targeted field fix may mean a sibling field exists — possibly more than once, and not necessarily even the same field *kind*

**When it bites:** A "closed registry" or "unsupported value" crash
hypothesis (some field must match a known table, or the load/render path
builds a null/degenerate resource otherwise) has real disassembly evidence
behind it, a fix patches that exact field, and a live A/B retest produces
the **byte-for-byte identical** crash (same PC, LR, fault address, *and*
register values like a heap pointer) — not just "still crashes," but
crashes with zero measurable difference. The instinct is either to distrust
the whole theory, or to assume the build didn't apply correctly. Neither is
right, and — this lesson's second half — don't assume the *next* plausible-
looking candidate field is right either just because it's superficially
similar to the first two attempts.

## What actually happened

Fire Emblem Warriors: Three Hopes (Switch) crashed loading a spliced-in G1M
model with a null-pointer-shaped fault whose address matched
`NULL + 9984*16 == 0x27000`. This took **three** rounds to actually solve,
and the first two both hit the identical-crash tell described above:

1. A `re-oracle` escalation traced the fault to a closed, executable-baked
   registry of 18 valid mesh-group shader-permutation *names* (a 16-byte
   ASCII field). A fix renamed the model's 9 unsupported names to real
   corpus names — verified byte-exact, structurally clean, nothing else
   moved. Live-tested: **identical crash**, down to a specific heap-pointer
   register value that could only recur if the exact same allocation
   sequence ran to the exact same point. That specificity is the tell: the
   patched field was never consulted before the fault.
2. Reasoning "look for a second, sibling name-keyed table," a previously
   wholly-undecoded sibling chunk (`GM1G` inner chunk magic=3, "ShaderParam")
   turned out to hold **another** name-keyed table — per-material named
   float/int parameters (`rampIndex`, `wtBldPrms`, etc.). A corpus census
   (705 real G1M instances) found exactly 26 valid names; the spliced
   model's block carried 6 FE3H-only names absent from all 705, in 100% of
   its materials — a clean, zero-deviation, *and completely wrong* result.
   This was staged as a fix and, per the brief's own author's honest
   assessment, was plausible enough to recommend installing — **before** a
   second `re-oracle` escalation (launched in parallel, not gated on this
   result) returned with the real answer.
3. The **real** cause: the mesh-group sub-entry's own `flag`(u16) +
   `nunId`(u32) fields — **not a string at all**, a numeric id — mark FE3H
   NUN-cloth physics bindings (`nunId` 20000-20002). FE Warriors' engine
   indexes a small parameter table with `nunId - 10000` and never range- or
   null-checks it; real FE Warriors data only ever uses `nunId` in `0..6` or
   `10000..10007` (table indices `0..7`), so Byleth's `20000..20002` (indices
   `10000..10002`) index far outside any real table's bounds.

The second hypothesis had exactly the same shape of evidence as the first
(disassembly-adjacent reasoning + a clean corpus census with zero
deviation) and was still wrong. The real fix touched a field two full
"kinds" away from the first guess: not a name, not even a string-shaped
value — a plain numeric id whose *range*, not its presence in a lookup
table, was the actual defect.

## The generalizable lesson

1. **An identical-down-to-register-values crash after a targeted field fix
   is strong evidence that field was never read on the path that faults** —
   not evidence the registry-lookup *mechanism* is wrong, and not evidence
   the build is broken. Verify the build first (cheap: re-read the patched
   bytes with the project's own read-only parser) before doing anything
   else.
2. **A clean, zero-deviation corpus census for a second candidate field is
   suggestive, not dispositive.** It has exactly the same *shape* of
   evidence as a correct finding and can still be a coincidence — this
   project's own census of 26 "valid" ShaderParam names lined up perfectly
   with a model that violated all 6 missing ones, and was still the wrong
   table entirely. A census confirms a field is *anomalous*; it doesn't by
   itself confirm that field is *read on the crashing path*. Where
   possible, prefer (or additionally get) actual disassembly proof the
   candidate field's *bytes* are the ones loaded into the faulting
   registers — which is what the second escalation this time actually
   provided (tracing `[cmd+6]`/`[cmd+0xa]` all the way from the mesh-group
   parser's write site to the crash function's read site).
3. **Don't assume the fix must be the same field *kind* as the first
   attempt.** Both wrong hypotheses here were "an ASCII name string not in
   a closed vocabulary." The real bug was a numeric id whose *magnitude*
   (not membership in a name table) was out of range. When a second
   same-kind candidate also turns out plausible-but-maybe-wrong, don't
   default to a third same-kind search — widen to *any* field in the same
   record shape (numeric ids, counts, flags), especially ones a reference
   decoder already knows about but has never validated the *values* of.
4. **When two escalations are run because the first's fix wasn't validated
   yet, keep both threads honest**: stage the new candidate but don't
   install it as "the fix" until it's independently re-verified (per
   `verify-escalation-artifacts-not-just-claims.md`) — this project's own
   practice of independently re-deriving a fresh, more complete corpus
   census (finding the real value bands `0..6`/`10000..10007`, not just the
   3 exact values re-oracle happened to report) is what turned "escalation
   says X" into "X, confirmed against raw bytes with a stronger census than
   the escalation itself ran."
