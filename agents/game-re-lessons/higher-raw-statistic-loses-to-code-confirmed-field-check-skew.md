# A wrong candidate field can outscore the code-confirmed right one on a raw resolution-rate statistic — trust the disassembly, then explain the score, don't re-rank by it

**When it bites:** two or more candidate record fields are being ranked by
percentage-match against an already-confirmed oracle value set (a name
table, an id enumeration, a directory), and the top-ranked candidate has
no independent code-level (disassembly) confirmation while a lower-ranked
one does — before trusting the ranking, or feeling any doubt about the
already-confirmed field, check whether the top candidate's own value
distribution is dominated by one value that also happens to be common in
the oracle set.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a battle move-entry's
`+0x09` byte was independently confirmed, by direct disassembly, as the
argument fed into a directory-search loop matching the game's own
animation-id enumeration — five structural facts lined up exactly with
the already-solved animation-directory format (count field position,
entry stride, key-byte position), and a null-controlled corpus check
(the field vs. its three sibling directory bytes) resolved at 94.57%
against 0.30%/0.15%/0.00%, a clean, decisive result on its own. A sibling
field in the same 20-byte record, `+0x11` (independently confirmed by a
*different*, unrelated disassembly trace to be a "combo-gauge
contribution" value with its own real consumer elsewhere), was checked
against the identical animation-id set purely as a side curiosity and
scored **96.38%** — nominally *higher* than the code-confirmed field's
94.57%. Investigating why: `+0x11` is one constant value (`10`) in
~96% of real entries, and `10` is also one of the animation system's
own common ids, so a plain "does this value appear in the oracle set"
test racks up a high score almost entirely from that one coincidental
overlap — not from `+0x11` genuinely functioning as an animation id
anywhere in the code.

**The fix, in order:**
1. Never let a naive resolution-percentage alone override a field whose
   role is independently pinned by disassembly — the code trace is
   ground truth, the percentage is a corroborating signal, not the
   other way around.
2. When a statistic *does* surprise you (a candidate scores higher than
   the confirmed answer, not just close), don't silently drop the
   surprising number — explain it. Check the candidate's own value
   histogram for a single dominant value; if that value is also common
   in the oracle set, the high score is a coincidence of skew, not
   evidence of a real relationship.
3. Record the coincidence in the write-up rather than omitting it. A
   surprising-but-explained statistic is useful context for the next
   session (it forecloses "but field X scores higher, are we sure?"
   before anyone has to re-derive the explanation), and silently
   dropping an inconvenient number erodes trust in the rest of the
   write-up's honesty once someone else re-runs the same probe and
   notices it wasn't mentioned.

**A second instance, same shape, different domain: deciding whether to
extend a confirmed rendering-mode fix to a sibling enum value.** Confirmed
on Dragon's Crown (PS3, `vanille`): an already-verified fix (render
`FMBS` part `mode === 1` with additive/glow blending — confirmed by
disassembly-equivalent evidence: an instrumented render pinpointing the
exact offending part, plus a positive visual match on two independent
models) has a corpus-wide "opaque near-black texture crop" statistic of
3.25%. A sibling value, `mode === 6`, scores *higher* on the identical
statistic (11.11%) — tempting to extend the same additive-blend fix to
it on the strength of that stronger number. Direct evidence overruled the
statistic: visually inspecting real `mode === 6` examples found dim, dark
*background/scenery* art with none of `mode === 1`'s "bright highlight on
transparent/black" signature — applying additive blending there would
plausibly erase legitimate dark art rather than fix anything. The
statistic alone couldn't distinguish "these opaque-black-crop parts are
glow sprites" from "these opaque-black-crop parts are just dark scenery,"
because both produce the same texture-sampling signature; only looking at
the actual pixels could. **Same rule as the field-identification case**:
a stronger raw statistic for a candidate extension is not itself evidence
the extension is correct — require the same class of direct/positive
evidence (here: a visual glow signature, not just a matching crop
percentage) that justified the original, narrower fix before broadening
its scope, and record the rejected extension with its reasoning rather
than silently limiting the fix and leaving the "but mode 6 scores higher"
question for the next session to re-ask.

This differs from a **true tie** (see
`tied-primary-signal-needs-orthogonal-secondary-signal.md`, where two
candidates compute the *identical* score and the fix is to find an
orthogonal signal) and from a **thematic-skew refutation of an index
hypothesis** (see `cross-stat-correlation-refutes-index-hypothesis.md`,
where an in-range-but-wrong-flavor result argues the field isn't an index
at all) — here the statistic is not tied and not obviously wrong-looking
on its face, it is simply outranked by a worse field due to a skewed
value distribution, and the resolving move is to lean on independent
code-level provenance you already have rather than distrust it.
