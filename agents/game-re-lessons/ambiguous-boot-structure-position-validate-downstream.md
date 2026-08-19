# Boot-structure position ambiguous by a few bytes — validate the downstream structure, don't trust the header offset

**When it bites:** locating a boot/load structure (a DOL header, a
filesystem root, a partition descriptor) whose position is ambiguous by
a few bytes — a preceding structure's trailer can look like a leading
zero field of the next one — and the offset you pick determines whether
every downstream parse succeeds or produces garbage.

Wii partition (Muramasa): main.dol's header position was ambiguous
between 0x3E5FC and 0x3E600 (an apploader trailer u32 of zeros could
read as a leading header field). Both interpretations produced a
plausible-looking DOL header with coherent section tables and identical
computed size; only one produced a FST that parsed (2,736 entries whose
names resolve). Heuristic field checks (magic, section-0 offset, mem
address) could not distinguish them; the FST parse could.

Fix: when a position is ambiguous, make the *downstream* structure the
arbiter — try each candidate offset and keep the one whose dependent
structures (FST entries, name table, directory records) validate
end-to-end. Require a substantial validation (e.g. ≥100 directory
entries with resolvable names), not just "doesn't crash": a misaligned
parse can pass vacuously (all entries reading as zero-name rows).
Validate against real structure, not heuristics.
