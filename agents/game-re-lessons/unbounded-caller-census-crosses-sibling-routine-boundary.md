# An unbounded whole-image caller census can mistake a big routine's own internal call sites for external callers

**When it bites:** a per-object-type/per-state routine's own internal
helper subroutine gets a caller census (a byte-pattern scan for the
helper's own call-instruction bytes across the whole binary, per
`shared-subroutine-reached-from-inside-type-body-not-entry-stub.md`'s own
recommended fix), and the hit list spans a suspiciously wide address
range — tempting an "engine-wide shared mechanism, called from many
unrelated object types" conclusion, before checking whether that wide-
looking range is still inside the one routine you started from.

## What went wrong

D&D: Shadows over Mystara (CPS2, `kolbold`): a per-object-type dispatch
table gives every large-monster type's own routine a bounded address
window — type N's routine runs from its own dispatch-table entry to the
*next* entry's address (e.g. type 14/19's routine: `[0x8fae4, 0x91530)`,
derived directly from the dispatch table two rows over, sitting right
there in the same table already used to find the routine in the first
place). Nobody computed that upper bound before running a caller census
on a helper found deep inside that routine's own state-0 body.

The unbounded whole-image census found "15+ callers spanning
`opcodes+0x8fda6` to `opcodes+0x91406`" — a wide enough spread to look
exactly like a genuinely shared, engine-wide primitive used by many
unrelated object types, and was reported that way, twice (once by the
session that ran the census, and again when a follow-up structural diff
of the "shared" mechanism's own tables found near-identical content and
took that as further confirmation of "shared, not type-specific"). Both
conclusions were wrong: every one of those 15+ call sites was still
inside type 14/19's own single ~0xA4C-byte routine. The routine is simply
large, with many internal call sites into its own frequently-reused
internal helper — indistinguishable from genuinely external callers by
address alone, unless you first know where the routine itself ends.

## Fix

Before accepting "many callers spanning a wide address range" as evidence
a helper is shared/engine-wide, derive the calling routine's own address
window from its dispatch/jump table first (the next table entry's target
address is the routine's end, for any dispatch scheme where routines are
laid out contiguously and addressed by table — a common pattern for
per-type/per-state object behaviour in this class of engine). Then check
whether the "wide-spanning" caller list is actually still entirely inside
that window. A caller list that looks alarmingly broad only when compared
against the WHOLE ROM can look completely mundane (all internal) once
compared against the one routine's own real size — and a routine handling
a rich per-type state machine (many sub-states, many conditional
branches) can easily span several KB, wider than intuition expects from
"one object type's code."

This is the natural sequel to
`shared-subroutine-reached-from-inside-type-body-not-entry-stub.md`,
whose own recommended fix (an unbounded whole-binary census for the
callee's own call bytes) is exactly right for *finding* a shared
primitive — but produces exactly the kind of wide-looking hit list this
file warns needs one more check before its width is trusted as evidence
of sharing. It's also a companion to
`sibling-functions-outside-callgraph-scope.md` (a caller/callee trace
scoped too NARROWLY misses a sibling) and
`common-prologue-scan-fallthrough-false-positive.md` — together these
three cover both directions a call-graph census's implicit scope
assumption can be wrong: too narrow (misses a real caller/input source)
and too wide (mistakes a big routine's own interior for the outside
world).
