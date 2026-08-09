# A newly-added auxiliary field that draws a near-constant, resource-independent value can silently break an existing "every field in range" well-formedness gate

**When it bites:** adding a new optional/derived field to a classifier or
decoder's existing well-formedness/validity gate (an `isWellFormed()`-style
function that ANDs together "every referenced index/offset must be in range
for *this* record's own size" checks across several fields) — especially
when the new field's value comes from a shared, game-wide table position
(a fixed table row, a global constant, a "the same byte works for every
instance" convention) rather than being derived from the specific
record/resource's own properties (its own frame count, length, entry count).

## What happened

WIME's (middilgard project) per-race FRML animation-VM classifier already had
`isWimeAnimVmWellFormed()`, a gate requiring `idle`/`walk`/`combatReady` to be
non-empty and every frame index across all traced fields to be `< frameCount`
for the specific resource being classified — correct and necessary, since a
non-standard race's row (Balrog) genuinely fails this and must fall back to a
geometry heuristic.

A later session added three more traced fields, one of which (`payRespect`)
always draws literal frame index 10 from a shared "post-outcome reaction
block" region of the table — real content, confirmed against ground truth,
and correct for every race whose FRML resource has 11+ frames (the standard
troop-sprite template). The natural-looking fix was to fold this new field
into the *existing* gate, the same way the original fields were checked.

This broke a previously-correctly-classified resource: `AAnims.res` FRML #7
(ents) has only 10 frames (valid indices 0-9). Its `idle`/`walk`/
`combatReady`/`attackSwing`/`death` content was all real, in-range, and
would have passed the gate exactly as before — but `payRespect`'s hardcoded
frame 10 is now out of range for this specific resource, so the *whole*
`isWimeAnimVmWellFormed()` call returned `false`, discarding the entire
confirmed classification and silently falling back to the (weaker,
`'hypothesis'`-tier) geometry classifier for a resource that had nothing
actually wrong with its core fields.

The bug was caught only by re-running the full asset-build manifest and
diffing per-resource segment lists against the pre-change baseline — the
unit test suite's synthetic fixtures never modeled a resource this short, so
`npx vitest run` stayed green throughout.

## The fix, and the general rule

Exclude fields whose value is a shared/near-constant table position (not
derived from the record's own size/count) from the overall well-formedness
gate. Instead, range-check each such field **individually**, right where it
is turned into its own output segment/field, and simply omit that one
segment/field when it doesn't fit — never let it invalidate the fields that
*did* pass. In code terms: `isWellFormed()` stays scoped to the fields that
are genuinely load-bearing for "is this a well-formed record at all"; an
auxiliary field's own `frameIndex < thisResource.frameCount` check lives next
to the `if (field.length > 0) segments.push(...)` call that emits it.

This generalizes beyond animation VMs: any RE pipeline with a "confidence" or
"well-formedness" gate that ANDs range checks across multiple fields is at
risk the moment a new field is added whose value comes from a shared
constant/table row rather than the specific record being validated. Before
folding a new field into an existing all-or-nothing gate, ask whether its
value scales with *this* record's own size — if not, gate it separately.
