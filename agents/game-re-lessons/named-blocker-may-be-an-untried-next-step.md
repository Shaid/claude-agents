# A doc's own precise "why this is still open" sentence can be the untried next step, not a real blocker

**When it bites:** an item has been left at `hypothesis`/open for several
rounds with a *specific, concrete* stated reason (not a vague "needs more
work") — especially "handler/routine X is not traced past point Y" or "no
corroborating sibling exists" — and a fresh pass is deciding whether to sweep
many rows looking for an untried *technique* rather than re-reading this one
row's own sentence for a literal next action.

This differs from the doc-citation-staleness family
(`doc-self-cross-reference-before-fresh-disassembly.md`,
`tracker-prose-is-not-evidence.md`): those are about a citation being *wrong*,
*stale*, or attributed to the wrong item. Here the citation is entirely
correct — the doc accurately says "not traced" — but the concrete action it
names had simply never been performed, despite being cheap.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project), round 197: the
field-scripting VM's `scene-script-vm.md` had left opcode 167 `CAMERA_SCAN`
at `hypothesis` for ~10 rounds with two named reasons: "what happens on a
match (or exhaustion) is not traced" and "no corroborating sibling opcode"
(the opcode has 0 real corpus occurrences, so no script data could confirm a
guess either way). Both were literally true and both were simply untried
steps:

1. **"Not traced" meant exactly that** — nobody had disassembled the ~15
   more instructions past the documented stopping point. Doing so (bit-20
   immediate/stack test, then the match and exhaustion branches) fully
   resolved the handler in one pass, no new technique needed.
2. **The "sibling" search had only looked at other opcodes' own dispatch
   HANDLERS.** The real sibling was a different opcode's own *installed
   per-frame task* (spawned by opcode 160 `TINT`, not part of its dispatch
   handler at all) that read/wrote the identical struct fields over the
   identical array/stride/count formula. Widening "sibling opcode" from
   "another handler" to "any code touching the same fields, including tasks
   and callbacks other opcodes install" found it immediately, and
   re-disassembling that routine fresh (not trusting the doc's own existing
   citation of it for an unrelated field) confirmed the match byte-exact.

**Fix:** before sweeping many open rows for a technique-toolkit gap, first
check whether any long-stuck row's own stated blocker is phrased as a
concrete, bounded action ("trace routine X to its end," "find a sibling
consumer of field Y") rather than a genuine unknown. If so, just do that
literal action — completing a partial disassembly, or widening a "sibling"/
"consumer" search past the one code-shape (handler, dispatch table entry)
it was originally scoped to — before reaching for a different technique or
escalating. A reason that's precise enough to *name* the missing step is
usually precise enough to *be* the missing step.
