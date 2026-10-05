# HUNK_RELOC32 operand hex comment shows IRA's resolved value, not the raw file byte

**When it bites:** Independently re-verifying an IRA `.asm` disassembly's
printed hex-comment column against the *raw executable file bytes* at the
same computed offset, for an instruction whose operand is an absolute-long
reference to a symbol in a **different hunk** (e.g. a CODE-hunk instruction
loading the address of a DATA/BSS-hunk global) — as opposed to a same-hunk
reference or a plain scalar immediate.

## What went wrong

On a Midwinter 2 (Amiga) session, an already-established project convention
("hunk0 CODE `file_offset = ORG + 0x2C`, spot-checked 13/13 reliable")
was being used to independently re-verify specific citations by reading raw
file bytes at the computed offset and diffing them against the `.asm`'s own
hex-comment column. The very first instruction of a routine matched exactly
(`MOVE.W #$0060,294(A6)` → `3d7c00600126`, found byte-for-byte at the
computed offset). The **very next instruction** —
`MOVE.L #LAB_1DDE,LAB_179F` (`.asm` hex comment `23fc00053988000385dc`) —
did not: the real file bytes at that exact, arithmetic-verified offset were
`23fc00009c80000032a4`. The same pattern repeated for two other citations
in the same session (`LAB_0939`'s and `LAB_0F9E`'s `MOVE.L #LAB_1DD9,...`
operands). This initially looked like a serious reliability failure in the
`ORG + 0x2C` formula itself, or in IRA's hex-comment column generally.

It is neither. It is **normal, expected relocatable-executable behavior**:
an absolute-long operand that references a symbol in a *different* hunk is
not stored as a final resolved address in the raw file at all — it's
whatever placeholder/hunk-relative value happened to be assembled in, which
gets **patched at load time** by a `HUNK_RELOC32` entry (base-hunk address
+ offset, added by the AmigaOS loader). IRA parses that same
`HUNK_RELOC32` table and, for readability, prints its **own internally
resolved address** (computed under its own assumed per-hunk load-base
model) in the hex-comment column — not the literal on-disk placeholder
bytes. A plain scalar immediate (`#$0060`) or a same-hunk CODE reference is
never relocated this way, so those hex comments *do* match raw bytes
exactly — which is why the first instruction's spot-check passed and gave
false confidence that the whole routine's hex comments were raw-byte
ground truth.

## The fix

- `file_offset = ORG + 0x2C` (or whatever the project's established
  per-hunk formula is) remains reliable for locating **where an
  instruction starts** — opcode bytes are never relocated, only specific
  operand fields within some instructions are. Keep citing instruction
  *positions* this way.
- Do **not** treat an absolute-long operand's printed hex value as
  raw-byte-verifiable when it references a different hunk (a DATA/BSS
  global from CODE, or vice versa). Cite it by **symbol name** (`LAB_1DDE`)
  and note the displayed address is IRA's resolved value, not a literal
  file byte.
- The **symbol-name identity itself remains trustworthy**: IRA derives it
  from the real `HUNK_RELOC32` table, not from guesswork, so two citations
  both naming `LAB_1DDE` really do reference the same relocated target —
  this is legitimate corroborating evidence for a data-flow claim (e.g.
  "routine A's write target is the same buffer routine B reads from") even
  though the literal hex digits shown for it aren't independently
  byte-diffable against the raw file.
- To independently pin down a relocated symbol's *runtime* address without
  trusting IRA's synthesized value, read the `HUNK_RELOC32` block itself
  (target hunk id + list of patch-site file offsets) rather than diffing
  hex-comment text.
- Same-hunk absolute references and plain immediates are unaffected — spot
  checking one of *those* successfully does not establish that a routine's
  *other*, cross-hunk operands will also raw-byte-verify.
