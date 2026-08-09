# Residue that clusters into recurring identical/near-identical word groups can mean the region is a program, not a table

**When it bites:** a data-record parser's leftover "gap"/"unexplained"
residue, when listed out, keeps producing the *same* short word groups over
and over (the same vertex-index tuple, the same small constant, the same
argument shape) at different file offsets — especially if a second-record-
type theory explains some of the residue but leaves a stubborn remainder
that still recurs this way.

Confirmed on Epic (Amiga)'s `.3D`/`.IGD` model format: after a `re-
codebreaker` escalation disassembled the game's own model-loading code, the
entire region previously parsed as "face records" turned out to be an
**executable display-list bytecode** — the game compiles the object once
after loading and an interpreter runs the opcodes every frame. One opcode
(21, a backface/orientation test) drives a **per-octant visibility decision
tree**: 8 leaves, each a different subset of the model's polygons selected
by view angle, laid out sequentially in the file (nothing is "compressed
away" for paths not taken — every byte is real, physically present data).
Because several polygons are visible from most of the 8 octants, the same
vertex-index groups (e.g. the same quad's 4 indices) appear in leaf after
leaf, at different offsets — exactly the "residue clusters recur" signature
that had earlier been read as an unexplained oddity of a still-incomplete
record grammar. The recurrence wasn't noise or a coincidence to explain
away; it was the visible fingerprint of a **decision tree re-emitting the
same drawable content down multiple branches**.

**The generalizable tell:** a table/record array's residue, when it's
*wrong-grammar* residue (a still-undiscovered record type, a bad stride, an
off-by-one base offset), usually looks locally structured but not overtly
*repetitive* — different records with different field values scattered
around. Residue that instead keeps reproducing near-identical word groups
verbatim at multiple unrelated offsets is a much stronger signal of
**control flow** (a branch/jump/conditional-skip structure re-visiting or
duplicating the same payload down different paths) than of a missing record
type. Reach for a disassembly of the region's *consumer* code (the loader,
compiler-pass, or interpreter that reads this file) before spending more
effort on structural-only parsing theories — a program only reveals itself
this way once you look for opcodes and branches, not fields and strides.
See also `packed-exe-mimics-variable-length-records.md` for the sibling
trap on the *executable* side (a packer's own commands mimicking data
records) and `reaudit-base-grammar-before-new-record-type.md` for the
process discipline that should trigger this check.
