# A doc's "open"/"TBD" claim can be stale if the working tree has uncommitted code

**When it bites:** starting RE work on a format/item the project's docs (or
`docs/<game>/TODO.md`) currently call open or unsolved — before writing a
single probe script.

Docs describe a *committed* understanding, but a prior agent session can
leave real, working progress **uncommitted** in the tree: a rewritten
decoder module, a consumer script pointed at it, even a passing `tsc`/lint —
without ever updating the docs or writing the new spec file the code itself
references. Reading only the docs in that state gives a confidently wrong
picture ("this is still open") and risks re-deriving from scratch a format
that's already cracked, sitting a few directories away.

Confirmed on Hunter (Amiga): the docs described the OB 3D format's
delta/extrusion section as "encoding not yet decoded," with 10 objects
left un-assembled. But `git status`/`git diff HEAD` on the extractor scripts
showed a complete, already-rewritten shared decoder
(`tools/hunter/ob-format.mjs`) already wired into both consumers, whose
header comment cited seven named engine routines by file offset as its
evidence — yet the doc it pointed to (`docs/formats/hunter-ob.md`) didn't
exist, and the three format docs still described the old, disproven model.
Running the code and then verifying its cited disassembly addresses
directly confirmed it was correct (220 objects, 0 out-of-range vertex
indices, vs. the old model's 10 broken objects) — a result that would have
been invisible from `Read`ing the docs alone, and that could have led to
hours of redundant re-reversing had the working tree not been checked first.

**Fix:** before starting RE work on any item the docs call open, run
`git status --short` and `git diff HEAD` on the project's relevant `tools/`
decoder files (not just the docs) for that format. If a decoder exists and
looks materially different from what the docs describe, run it and check
its output/citations before assuming the docs are current — code can be
ahead of docs just as often as the reverse.
