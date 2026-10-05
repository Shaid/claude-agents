# A field that looks like it has two unrelated roles inside a callee may be one coherent field once the CALLER'S gating logic is read

**When it bites:** disassembling a single function finds a per-object/per-
actor field read in two seemingly unrelated ways along two different
branches — e.g. tested as a boolean gate on one path and consumed as a
numeric value/delta on another — tempting a "dual role, not fully
understood" write-up. This is especially likely when only the CALLEE has
been disassembled and the branch selecting which path runs is driven by an
argument (a "mode"/"flags" word) computed somewhere else, not by the field
itself.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 212: a field-sprite
renderer's general-render-path function read `obj+0xee` two different ways
depending on which "render mode" branch it took — as a plain non-zero gate
in the default path (enabling a small pixel nudge) and as a rotation-angle
delta added into a computed angle in a separate rotation sub-path. A prior
round, having only disassembled this one function, filed it as a genuine
"dual role" open question. Disassembling the CALLER — the dispatcher that
computes the "render mode" word this function branches on — showed the
rotation branch is selected precisely when `obj+0xee != 0`: the exact same
field the callee later reads as an angle. The "two roles" collapse into
one: `obj+0xee` is a single, coherent "extra static rotation angle, 0 =
none" field, and its role in the DEFAULT path's gate was never a second,
independent role at all — it's simply what "no rotation" (angle is zero)
happens to also mean for an unrelated cosmetic nudge that was gated the
same way by coincidence of both defaulting to the same field.

**Fix:** before writing up a field as having multiple, only-loosely-related
roles based on one function's internal branches, trace back to whoever
computes the mode/flags argument that SELECTS between those branches. The
selecting logic often reveals that both "roles" are downstream
consequences of a single upstream fact about the field (its zero-ness, its
sign, its magnitude band) rather than two independent design decisions that
happen to share a byte offset. This is a different failure mode from
`verified-callee-internals-leave-caller-edge-unchecked.md` (which is about
an *unconfirmed calling relationship* despite thorough callee checks) —
here the calling relationship is known and even the callee's internals are
fully confirmed; what's missing is disassembling the specific CALLER
computation that ties the callee's two branches together semantically.
