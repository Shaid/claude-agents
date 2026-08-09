# A committed IRA `.asm` can look like a normal disassembly while covering ~1% of the binary

**When it bites:** about to trust grep/text-search results over a committed
IRA `.asm` file as representative of the whole binary — especially when a
sweep comes back with a suspiciously clean negative for something you have
independent reason (a string xref, a known caller, a cross-platform port's
equivalent function) to believe exists in code somewhere.

## What went wrong

A project's `.cnf` (the durable IRA config — see `game-re-tooling/amiga.md`'s
"large hand-optimized binary" entry for the fix mechanism itself) declared an
explicit `CODE` range for only ~5.5 KB of a 351,292-byte CODE hunk — a small
cluster IRA's `-preproc` auto-detection happened to find. The remaining
~345 KB (98.4% of the hunk) fell back to undifferentiated `DC.L` hex in the
committed `.asm`. This was invisible as a problem across **two separate RE
sessions**, weeks apart, because the `.asm` file didn't look broken: it had
real labels, some real instructions, no parse errors — just silently
near-total coverage loss. Both sessions ran ordinary text/regex sweeps over
it looking for a specific consumer function, got a clean "not found," and
moved on. The function existed the whole time, entirely inside the
undeclared span; a third session only found it by bypassing the `.cnf`
entirely with a raw capstone/radare2 linear pass, then traced the false
negative back to the coverage gap.

This is a distinct trap from "the `.asm` doesn't exist yet" (which is
obviously incomplete) or from "`-preproc` misclassified this one function"
(a local, discoverable error) — it's "the `.asm` exists, looks plausible,
gets committed and trusted as a search surface for months across multiple
sessions, while actually covering ~1% of the binary."

## Diagnostic (cheap, do this before trusting the sweep)

Before relying on grep/regex results over an existing committed `.asm`,
check what fraction of the source binary's code-hunk byte range is actually
declared `CODE` in the paired `.cnf`:

```bash
grep '^CODE' Target.cnf   # sum the declared ranges
# compare the sum to the hunk's real payload size (from the hunk header)
```

If the declared-code total is a small fraction of the hunk size, the `.asm`
is not a reliable "not found" oracle — a clean negative there proves nothing
about the real binary. Do this once per binary before the first sweep,
especially for large (>50 KB) hand-optimized binaries with inline
string/data literals interleaved with code (the shape that defeats
`-preproc` — see the tooling file for the fix). The fix itself is usually a
single `.cnf` edit (extend/merge the `CODE` ranges to cover the whole hunk)
plus a `-config` regenerate — cheap once someone realizes it's needed;
confirmed taking a 351 KB hunk from ~1.5% to 99.47% declared-code coverage
in one edit + regenerate, turning 93,841 lines of real instructions visible
that were previously flattened to `DC.L` hex.

## Variant: hundreds of narrow `CODE` islands, not one big undeclared span

A `.cnf` doesn't have to look sparse to have this problem. Gunship 2000
AGA's `gs.asm` (435 KB, 131-hunk MANX binary) had a `.cnf` with **~430
separate `CODE` range declarations already** — `-preproc`'s recursive
descent had found a huge number of individual small routines (each reached
via its own call-site xref) but never walked the straight-line code
*connecting* them, leaving hundreds of small DATA-classified gaps (tens to
low-thousands of bytes each) scattered throughout the file, several of
which held real code (`DC.L`/`DC.W` hex disguising `RTS`/`MOVEM`/`JSR`
opcodes). One such gap (sound-effect-trigger dispatch thunks) was flagged
and fixed by merging it into one `CODE` range; **a broader post-fix sweep
for the same disguised-opcode signal found it recurring in several other,
still-untouched gaps elsewhere in the same file** — fixing the one flagged
region did not mean the `.cnf`'s fragmentation problem was solved
elsewhere. A `.cnf` with a large *count* of `CODE` ranges is not evidence
of good coverage by itself; sum the declared ranges' total byte length
against the hunk size (same diagnostic as above) and/or grep the whole
`.asm` for disguised-opcode hex (`$4E75`/`$4E56`/`$48E7`/`$4EB9`/`$4EAD`/
`$6100`-range inside `DC.W`/`DC.L` lines) before trusting that a single
flagged-and-fixed region means the binary's disassembly is now reliable
end to end.
