# A census for code that *constructs* a value is blind to a consumer that reads it pre-packed from a data table

**When it bites:** an exhaustive, honestly-run code census for "does any
code ever build/assemble bit-pattern X" (a hardware register word, a
texture-page/CLUT selector, a pointer, a packed flags byte) comes back
negative — and especially when a **second**, differently-scoped census
(a different opcode family, a different addressing mode, a different
"kind" of consumer entirely) *also* comes back negative for the same
target, tempting a confident "no consumer anywhere in the executable"
verdict.

Parasite Eve (PSX, `parasiteeve`): chunk1 of the actor-package container
held two real, human-authored VRAM texture pages (VRAM x=768/832). A
`ghidra-disasm` escalation exhaustively censused every code path that
*constructs* a PSX `tpage`/texpage bitfield (the usual shape: separate tx/ty/
mode fields shifted and OR'd together in code) and found only two such
paths, neither ever producing tx=12/13 — a clean, careful, correct negative
for that specific search axis. A second session broadened the search to
every 2D VRAM-*transfer* primitive (`LoadImage`/`StoreImage`/`MoveImage`,
all 10 call sites in the executable) and again found nothing touching that
region. Both censuses were exhaustive and honest for the code family they
searched. Both were false negatives. The real consumer
(`FUN_80066f60`/`FUN_80077a64`/`FUN_80077aa4`, part of a per-actor-package
"tile-scatter" background compositor) never constructs a tpage value in
code at all: it reads one **already packed** — tx/ty/clut/u/v bit-packed
into an 8-byte data record — straight out of a per-package data table, and
splices a `SPRT_16`+`DR_TPAGE` GPU primitive directly into the ordering
table using those bytes verbatim. There is no bitfield-assembly instruction
sequence anywhere to find, because the "construction" already happened at
authoring time, not at runtime.

This is a different failure from `narrow-opcode-form-census-false-
negative.md` (which is about missing an addressing-mode/register-class
*variant* of a compiler-emitted pattern — still a code-side miss). Here
there is no code shape to miss at all for the data-driven path; widening the
opcode/addressing-mode coverage of a code census can never find it, no
matter how exhaustive, because the target isn't assembled by any
instruction sequence.

**Fix:** before writing up "no consumer constructs/produces value X" as a
load-bearing negative, separately scan **data regions/tables** (not code)
for the literal target bit pattern (or its component subfields, at the
byte-position layout a plausible record format would use) sitting
pre-packed in already-identified per-object/per-record data — especially
tables you have already partially decoded for an unrelated reason (here,
chunk3's own slot 6, already flagged as a "camera/trigger/tile" system by
an earlier structural pass that stopped short of tracing its texture-
selector fields to a VRAM region). A code census and a data census answer
genuinely different questions, and only running the first — however many
times, however broadened — cannot substitute for the second. The tie-
breaker that actually cracked this case was not a third code census but
rendering the real corpus-wide output as visual ground truth (see
`verify-escalation-artifacts-not-just-claims.md`'s sibling instinct: when
two structurally-different code searches agree on a negative, prefer a
content-level check — a render, a decode-and-inspect — over a third search
of the same kind).
