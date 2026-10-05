# A per-object field byte can hold a stable identity value in one state and an unrelated transient scratch/timer value in another — scope extraction to the narrow window, not the whole function

**When it bites:** a per-object-record field offset (already suspected or
confirmed to encode a stable per-instance "identity"/id/class value in one
code path) is about to be bulk-extracted by scanning a whole
behaviour-routine, a whole state-machine body, or the whole binary for
writes to that same offset — especially when a handful of the extracted
values don't fit the pattern the rest do (break an otherwise-clean
arithmetic progression, or duplicate a value that "shouldn't" repeat).

Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`): a per-character-
object field `$2e(a0)` was set, immediately before each object type's own
call into a shared HP-init subroutine, to a small integer that turned out
to be a real "creature/visual identity id" consumed by three parallel
per-id pointer tables (a reach/anchor-point mechanism for a two-character
grab/combo-attack calculation). For most types this value was simply
`type id + a per-pool constant` — but the *exact same byte offset* is also
used, in a completely unrelated function belonging to a different object
class entirely, as an ordinary per-object countdown timer: `tst.b
$2e(a0) / beq ... / subq.b #1,$2e(a0)`. A wide, whole-routine or
whole-image scan for `move.b #imm,$2e(a0)` cannot distinguish these two
roles — it will happily report a "creature id" harvested from a countdown
initialisation in some unrelated state, indistinguishable in the raw
byte pattern from a genuine identity write.

**Fix:** when extracting "the value of field X" for a semantic-identity
purpose, don't scan a whole function or the whole image for every write to
that offset. Scope the search to the exact code window where the semantic
role is independently known to be genuine — here, "between this object
type's state-0 entry point and its own already-confirmed call into the
shared HP-init subroutine" (a call target pinned down in an earlier,
unrelated investigation). Writes outside that window are not evidence
either way; they may be the same role reused legitimately, or a completely
different, coincidentally-colocated role. A good tell that contamination
has happened: values that don't fit an otherwise-clean derived pattern (a
duplicate of a value from an unrelated instance, a value miles outside the
range every sibling instance produces) are a signal to re-derive with a
tighter window rather than to accept the outlier at face value — but also
don't discard every outlier automatically, since a minority of them (here,
two of five) turned out to be genuine and informative once each half of
the duplicate pair was independently re-confirmed to precede its own real,
correctly-typed follow-on call.

This generalizes past 68000/CPS2: any engine that reuses a fixed
per-object struct offset for different purposes depending on which state
or object-type code is currently executing (common wherever object records
are a flat byte array with no per-type schema) creates exactly this trap
for any census-based field-value extraction.
