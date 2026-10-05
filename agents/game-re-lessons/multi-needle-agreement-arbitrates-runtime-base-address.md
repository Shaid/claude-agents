# Locating a loaded file's true runtime base in a large memory dump needs several independently-sized needles to agree, not just one

**When it bites:** you need a data file's live base address inside a large
captured memory image (a savestate's RAM chunk, a heap dump) to read
runtime-mutated state, and a byte-exact substring search for a short slice
of the file (its header, or the first N bytes of one section) returns more
than one hit — or returns exactly one hit and you're tempted to trust it
without checking further.

Confirmed on KGB (Amiga, `wyrm`): locating a chapter's loaded `.cma` file
inside a savestate's Z3 fast-RAM dump, a search for the file's 32-byte
header found **two** candidate base addresses. Searching for progressively
larger, independently-chosen static (non-runtime-mutated) byte ranges from
elsewhere in the same file — a 256-byte slice of a different section, then
another, then another — one candidate address kept matching all of them
exactly, while the other stopped matching as soon as a needle bigger than
the header was tried. The failing candidate was a coincidental partial
match (small needles have a non-trivial false-positive rate against ~256MB
of memory), not the real load address. Requiring **every** independent
needle to agree at the same base — not just the first one tried — is what
told them apart; the correct base was then cross-validated a second way
(reading the "live" bytes at that base reproduced an existing,
previously-unverified claim about which sections of the file mutate at
runtime, byte-for-byte).

**Fix:** when locating a runtime base address by string search, don't stop
at the first match, and don't rely on one small needle (a header, a magic,
a short prefix) alone. Search for several independent byte ranges spread
across the file — ideally from regions already known to be static/
unmutated, so they still match the pristine on-disk bytes at runtime —
and require the same base address to satisfy all of them. A candidate
that matches only the smallest needle is very likely a coincidence, not
the real location, especially against a multi-megabyte haystack.
