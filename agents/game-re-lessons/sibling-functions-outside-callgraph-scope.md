# An exhaustive caller/callee trace from a confirmed node can still miss the answer — it can live in a sibling

**When it bites:** you've exhaustively traced every caller AND every callee of
a confirmed dispatcher/consumer function (via a sound method — e.g. a complete
`d16(PC)` displacement scan, not a narrow opcode census) looking for where its
inputs come from, found nothing but static tables and arithmetic, and are
about to write up "no data-dependent source exists" or "this consumer draws a
fixed backdrop."

Caller/callee tracing implicitly assumes a function's own inputs are either
computed by its ancestors (something in the caller chain) or delegated to its
descendants (something it calls). That assumption breaks when a **parent
function fans out to several independent sibling evaluators** and only passes
each one's *result* into the node you're tracing — the siblings are never a
caller of your node (they're called by the same parent, one level up) and
never a callee (your node never calls them either). No amount of
caller-graph-upward or callee-graph-downward walking from the node itself can
ever reach them, no matter how exhaustive the search technique.

Confirmed on Wizardry 6 (Amiga): a per-cell maze-piece dispatcher
(`CODE+0x9b58`) took ~9 "wall-type code" arguments. An exhaustive
bidirectional trace of its entire caller graph (5 call sites, all inside one
outer renderer function) and callee graph (a deferred-draw helper, its own
30-slot record array, two consumer loops) found every data-dependent branch
resolving to position-parity arithmetic or static lookup tables with no
writer — a structurally complete but wrong "the renderer draws a fixed,
non-cell-content-driven backdrop" conclusion. The real per-cell evaluator
turned out to be three **sibling** functions, called directly from the same
outer renderer at the same call depth as the dispatcher, which computed the
wall-type codes and only handed the dispatcher their results as plain
arguments. Escalating with the full trace (rather than re-trying the same
scope with more effort) found them: the fix was widening the search to a
function-prologue census of the whole containing address range
(`4E 55` = `link.w a5` on 68k) to enumerate *every* function the parent calls,
not just the one already confirmed.

**Fix:** when a caller/callee trace from a confirmed node comes up empty for
"where does this input come from," don't conclude the input is static —
census the *parent's* full call list (every sibling it invokes, not just the
node you started from) before writing up a negative. A negative here is only
as strong as your enumeration of the parent's own children, exactly the same
"shape vs. root" reliability gap as `negative-from-addressing-root-not-shapes.md`,
just one level up the call tree. This is also a specific instance of the
`jump-table-noop-means-handled-elsewhere.md` pattern (the reader you want is a
genuinely separate routine, not reachable from the one you've already found)
applied to ordinary call-graph tracing instead of a dispatch table.
