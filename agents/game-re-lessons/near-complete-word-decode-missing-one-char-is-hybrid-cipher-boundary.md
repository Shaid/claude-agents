# A byte-shift decode that recovers almost-complete real words, each missing exactly the same one character, means a two-part cipher — not corruption

**When it bites:** a single flat byte-shift (Caesar-style, `byte ± N`)
recovers dozens of recognizable-but-truncated English words from an
unidentified region, and every single one is missing exactly the same
position's character (commonly the first letter) — before concluding the
shift is "off by one," the data is corrupted, or widening the shift
search will fix it.

**Why it happens:** some formats encode a string with a genuinely
different single-byte transform at one boundary position (typically the
first character) than the rest of the string — e.g. reusing a project's
existing text charset shift for the "capital letter" position while the
body uses a separate, unrelated flat shift. A single-shift decode applied
uniformly across the whole string recovers the body correctly but turns
the boundary byte into garbage that doesn't survive an alphanumeric
filter, silently truncating the word by exactly one character every time.

Confirmed on Valkyrie Profile 2 (PS2)'s `PAMM` resource-directory
records: a flat `-1` byte shift recovered fragments like `"RAGONSCRYPT"`,
`"ALHALLA"`, `"ASTLE"` — real place names, each missing its own leading
letter. Dumping the raw byte immediately before one such fragment and
testing it against a *different*, already-confirmed project-specific
shift (this game's own main text charset, `ascii = stored + 0x1F`) gave
the exact missing letter (`0x25 + 0x1F = 'D'`, completing
`"DRAGONSCRYPT"`). The real scheme was a two-part hybrid cipher: first
letter `+0x1F`, remaining letters `-1`. Applying it whole-corpus (not
just the one example) recovered 43 distinct real English words across
404/404 real records — a decisive, whole-corpus confirmation, not a
one-off pattern match.

**The diagnostic and fix:** a consistent one-character truncation at a
fixed position, surviving across many independent instances, is the
tell — don't respond by widening the shift search on the *whole* string
(a project's existing single-shift hypothesis was already right for the
body). Instead, isolate the boundary byte specifically and test it
against every shift already confirmed *elsewhere in the same project*
(a UI text charset, a different table's own known offset) before
inventing a new one — the two transforms are often both already-known
constants from unrelated parts of the same game, just never combined
before.
