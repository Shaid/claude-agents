# A raw magic-byte scan can undercount a format's true corpus by orders of magnitude when a sibling magic exists

**When it bites:** you've counted a format's corpus population by scanning
raw bytes for one literal 4-byte magic (not walking the container's own
directory structure), and/or an "expected but missing" instance of a
per-asset format (a character with no skeleton, a clip with no animation)
tempts you to write it off as a genuine absence rather than checking
neighboring magics first.

Two compounding traps, both confirmed the same session (Drakengard/
Drakengard 2, PS2, Cavia Inc.): a format's magic can have a real, byte-
identical-structure **sibling magic** differing by exactly one byte (the
same "last-byte variant" habit already documented in
`sibling-magic-may-be-same-struct-zeroed-field.md`, but here the sibling
isn't rare — it can be the *majority* of the real corpus), and a **raw
magic-byte scan of a whole disc/archive undercounts a nested-container
format's population** relative to a structured directory walk, because a
byte-level scan's alignment/false-positive-avoidance logic can skip real
instances that a container-aware walk finds trivially.

Concretely: a skeleton format `CJFg` (11 instances found in Drakengard 1
by a straightforward magic search) has a real sibling `CJFd` — same
struct, decoded by the identical function — found only when a "why does
this one package have no skeleton" investigation checked neighboring
4-byte magics instead of accepting the absence (it turned out to be a
dragon companion's own skeleton, embedded build path literally reading
`dragon\caim\my_joint`). That alone looked like a rare, one-off variant
(1 `CJFd` vs. 11 `CJFg`) — until the same check was run on the sequel,
Drakengard 2: there, `CJFd` is the *dominant* magic, 524 of 528 total
skeletons (a scan for the literal `CJFg` string alone found only 4 — a
132x undercount). The same pattern repeated independently for the sibling
animation-clip format: `CMFd` outnumbers `CMFf` 4,233 to 18 on the sequel.
A third, related case in the same session: an earlier pass's raw
magic-byte scan of a mesh-geometry format across a whole disc found 2,691
instances and flagged 231 as an unidentified sub-format; a real container-
directory walk (following the archive's own nested-container structure,
not scanning bytes) found 12,938 real instances of the same base magic —
a ~4.8x larger true population, and the "sub-format" fraction resolved
cleanly to 304/12,938 (2.4%) once counted correctly, not 231/2,691 (8.6%)
as the shallow scan implied.

**Fix, two parts:**

1. **Always prefer a structured container/directory walk over a raw
   magic-byte scan for corpus-sizing claims**, whenever the target format
   is known to live inside a nested-container scheme. A raw scan is a fine
   first triage step, but don't publish a "N instances found" / "X%
   decoded" figure from one without cross-checking it against a walk that
   follows the container's own directory records.
2. **Before treating a "missing" per-asset instance of a format as a
   genuine absence, grep for every 4-byte magic sharing the same first 3
   bytes** (or whatever prefix the base magic shares across its own known
   variants) in the immediate neighborhood. If a sibling magic decodes
   with the *exact same* struct/function unmodified, extend the decoder's
   magic check to accept it (don't fork a second decoder) and re-run every
   existing whole-corpus percentage claim — they were computed against
   the undercounted population and need correcting, not just supplementing.

The corpus-count correction this produced touched several already-written
"100%" whole-corpus verification claims across multiple doc sections in
the same session — a good reminder that a "solved, N/N (100%)" figure is
only as trustworthy as the population-counting method behind the
denominator, not just the numerator's decode success rate.
