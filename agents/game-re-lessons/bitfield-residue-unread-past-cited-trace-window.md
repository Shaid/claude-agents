# A "not read anywhere" verdict on a bitfield residue may just mean the trace stopped early

**When it bites:** a doc says some bits of a packed struct/descriptor are
"not observed to be read anywhere" or "open/unused", especially when the
residue is wide (a double-digit number of bits) — too big to comfortably
believe is just padding — and the function that reads the *other* fields of
the same struct is long and only partially quoted in the doc's own trace
citation.

A trace pass naturally stops once it has explained the fields it set out to
explain — typically right after the last field write the pass was looking
for. But nothing stops the *same* consumer function from reading the *same*
struct a second time, later in its own body, for an unrelated purpose. If
the earlier pass's citation ends at that first return-to-caller-shaped point
rather than the function's actual end, "not observed to be read" silently
means "not read in the bytes I quoted", not "not read at all" — and it reads
as a much stronger claim than it is.

Confirmed on Vengeance of Excalibur's `SCEN` global descriptor: bits 0-14
(15 of them — large enough that "unused padding" should have been
suspicious on its own) were documented as dead after tracing
`_DrawScene`'s already-cited `paletteSelector`/`musicSelector` extraction.
Re-reading forward from that citation's own end line (not a fresh search)
found `_DrawScene` reading the exact same global-descriptor entry a second
time only ~20-90 lines further down its own body, splitting the residue
into two real fields (`entityXAnchor`/`entityYAnchor` — a scene's default
party-placement anchor), one of them consumed a few hundred lines later
still, inside the very same function's second loop.

**The fix:** before writing "not read anywhere" about a residue in an
already-open, already-cited function, re-read from the trace's own citation
end line to the function's actual `RTS`/`UNLK` — not a fresh whole-binary
search — and separately grep the raw storage location (the A4-displacement
global the confirmed fields were written to) across the *whole* disassembly
for any other reader, since the second consumer may live in a sibling
function entirely (as `entityXAnchor` did here, in an unlabelled block
inside a neighbouring routine). A residue too wide to be plausible padding
is a specific invitation to keep reading, not a green light to close the
question.
