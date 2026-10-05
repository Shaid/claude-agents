# Two RLE sub-cases can share an identical read primitive but differ only in which label their loop's back-branch targets

**When it bites:** a disassembled token/RLE decode loop has a "normal" case
and a "special/escape" case (leading value zero, a flag bit, a distinct
opcode range) that both call the SAME shared read-and-cache primitive
(a toggle-bit-gated "read a fresh byte or reuse an already-cached nibble/
byte" helper) right before a write+decrement micro-loop — and they look
structurally identical at a skim, tempting you to port both as "the same
shape, just entered differently" (e.g. "read once, then repeat-write N
times" for both). Also bites when a ported decoder terminates cleanly with
no crash and produces plausible-*shaped* output (right rough size,
recognizable-looking runs) for every input, yet consumes noticeably fewer
input bytes than a frame/record's own independently-declared payload
length — a symptom easy to misdiagnose as "wrong budget/length formula"
rather than "wrong per-iteration read count."

## What went wrong

Midwinter 2 (Amiga)'s `.cmp`/`.bin` sprite nibble-RLE codec (`LAB_0B8E`,
`hunter` project) has exactly this shape. A token starts with a run-length
nibble `r`:

- `r != 0` ("repeat-run"): read ONE more nibble as the colour value, then
  write it `r` times. The write+`DBF` micro-loop (`LAB_0B93`) loops back
  to **itself** — the colour value is read once and reused every
  iteration.
- `r == 0` ("literal-copy escape"): read a fresh run length `r'`, then for
  EACH of the `r'` output bytes read a NEW colour nibble and write it. The
  write+`DBF` loop (`LAB_0B99`) loops back to `LAB_0B97` — the
  toggle-bit-gated READ step, not the write-only step — so a distinct
  value is fetched every single iteration.

Both cases call the identical `NOT.W D7; BNE.S <read-fresh> / <reuse
cached>` primitive right before the loop, and both end in a `MOVE.B
D2,(A2)+; DBF D5,<label>` pair — the only difference between them, in the
raw disassembly, is which of the two adjacent labels that final `DBF`
names. A first hand-port flattened this: it treated the escape case as
"just re-read the run length, then reuse ONE fresh colour value for the
whole run" (mirroring the normal case's shape), which is wrong. The
decoder still ran to completion with no bounds error on every real file —
per-token output was always a plausible-looking run of one repeated byte
value — but it silently under-consumed the input stream every time an
escape token fired, since the real grammar demands `r'` distinct nibble
reads there, not one.

The bug was invisible to shape/plausibility checks (every decoded frame
still "looked like" recognizable sprite art in outline) and to a bare
"did it crash" check. It surfaced only once the decoder's *consumed input
byte count* was cross-checked against each frame's own container-declared
payload length (an independent, code-derived boundary from the format's
own offset table, not fitted to the decoder) across the WHOLE corpus, not
just the one or two hand-picked test files: consumption fell to roughly
half of the declared length on files that happened to trigger escape
tokens early and often, while files with few/no escapes looked deceptively
close to correct. The fix was found only by re-reading the RAW
disassembly text fresh, line by line, and diffing the two branches' `DBF`
targets side by side — not by re-deriving the algorithm from a prose
summary of "what the loop does" (even a careful one written by the same
session moments earlier), which had already silently flattened the
distinction once.

## Fix

When two sibling branches of a decode dispatch share a read/toggle
primitive and look identical at a glance, don't assume they're the same
operation entered two different ways — **diff the literal label each
branch's terminating loop (`DBF`, or any decrement-and-branch instruction)
targets.** A back-branch to the write-only step means "compute once, reuse
every iteration" (a true repeat-run); a back-branch to the read+toggle
step means "recompute every iteration" (a literal-copy run masquerading as
an escape of the first case). Verify the ported grammar with a
byte-exact input-consumption check against an independently-declared
length, run across the *entire* corpus — a decoder that always terminates
cleanly and looks shape-plausible per token is not evidence its escape
path is correct; only exact consumption is. See also
`rle-decode-succeeds-on-garbage.md` (decode completing without error is
not verification) and `length-invariant-blind-to-copy-semantics.md` (a
length check proves grammar, not content) — this file is the sharper,
narrower case where the length check itself is exactly what's needed and
what catches it, but only when it's run per-token-population-wide rather
than on a couple of samples that happen not to exercise the escape path
much.
