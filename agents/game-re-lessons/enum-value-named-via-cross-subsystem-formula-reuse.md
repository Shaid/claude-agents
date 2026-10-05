# An unnamed enum field can be named by finding it's a pure function of an already-decoded sibling field, especially when the formula is one this project already confirmed for an unrelated subsystem

**When it bites:** a fixed-record struct has an enum/small-integer field
whose consumer (a resolver function, a dispatch table) is already fully
traced at the instruction level, but the individual numeric *values* still
have no plain-English name, and the natural next step being proposed is
"trace each of N call sites' register dataflow in more detail." Before
doing that, census the field against every OTHER already-decoded field in
the *same record* for an exact (not just correlated) numeric relationship —
particularly one matching a formula this project has already confirmed
somewhere else, for a totally different subsystem.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a room's scroll-record
`kind` byte (values `0/10/20/130/140/150/30` plus free-choice "extra"
values) had its consumer (`fcn.80039ae8`, a logical-id-to-record-index
resolver) fully disassembled across all 16 real call sites, with the
resolver's own arithmetic completely solved — yet none of that explained
what "kind 20" or "kind 140" actually represented. The answer wasn't in
more call-site tracing: it was in the record's own **placement `order`
field**, already decoded and unrelated-looking. A corpus-wide census found
`order === 17*Math.floor(kind/10) + (kind%10)` for every non-main record,
**0 deviation across 25,287 placements, both discs** — and this formula
was not new: it was byte-identical to a repack rule the project's own docs
had already confirmed for a completely different scripted subsystem
(`SPAWN_PLATFORM`'s own `kind` parameter, turning a script literal into a
sprite-atlas frame index). Once found, the relationship immediately named
the enum's role: it is a **depth/z-order slot index** in a shared
project-wide base-10-grouped numbering convention, not a set of ad-hoc
content-type tags — the three fixed kinds below the main record always
draw first (background) and the three above it always draw last
(foreground), with the ordering coming directly from the formula, not from
guessed per-value semantics.

The technique costs almost nothing once the struct is already parsed
(a single script that recomputes every candidate cross-field relationship
across the whole corpus), and the reuse-across-subsystems detail is the
real payoff: a game engine that has one bit-packing/repack convention for
"kind" bytes tends to reuse it wherever a similar-shaped value needs to be
turned into an index, so a formula already confirmed for subsystem A is
worth testing against subsystem B's superficially unrelated stuck field
before assuming B needs its own fresh derivation.

**Fix, generalized:** when an enum/small-integer field resists naming
through its consumer's control flow, don't only widen the disassembly —
census it against every sibling field already decoded in the *same record*
for an exact algebraic relationship (not merely "these correlate," but "one
is a deterministic function of the other"), always with a positive control
(does the relationship hold for the value with the most examples) and a
negative control (does it *fail* for at least one value that should be
different, e.g. a "main"/default record whose corresponding field really is
independently authored) — a formula that holds everywhere including where
it shouldn't is itself a red flag, not a stronger confirmation. Before
treating a discovered formula as coincidental, grep the project's own docs
for the same numeric expression: a match to an already-confirmed formula
from an unrelated subsystem is strong, free corroboration that the finding
is a real project-wide convention rather than an overfit curiosity.
