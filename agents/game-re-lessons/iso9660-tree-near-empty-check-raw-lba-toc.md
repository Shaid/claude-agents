# A disc's ISO9660 tree with almost no files is not a bad rip — check for a raw-LBA archive

**When it bites:** a console disc image parses cleanly as ISO9660 (correct
`CD001` primary volume descriptor, no corruption) but the catalogued
directory tree lists only a handful of small files — nowhere near the
disc's actual multi-gigabyte size — and there's no UDF bridge to fall back
to either.

This is easy to misread as "the rip is broken" or "I'm parsing the wrong
volume descriptor," but on several commercial titles it's the real,
intentional layout: the developer bypasses the filesystem entirely for bulk
asset data, writing raw sectors directly and addressing them from the game's
own executable via absolute LBA — sidestepping ISO9660 directory-lookup
overhead. Confirmed on Valkyrie Profile 2: Silmeria (PS2, tri-Ace/Square
Enix, `~/Development/valkyrie`): the ISO9660 tree holds exactly 3 files
(`SYSTEM.CNF`, the main EE ELF, an IOP module image) totaling ~1.1MB against
a 4.6GB disc — **99.96% of the disc's bytes have no directory entry at
all.** `xorriso -indev <iso> -toc` reported `ISO offers: Only_ECMA_119` (no
Joliet/Rock Ridge/UDF), confirming there's no alternate filesystem view to
check either.

## What to actually do

1. **Confirm this is really the case** with an exhaustive (not sampled)
   non-zero-byte scan starting right after the last catalogued file's
   extent — a coarse/strided scan can badly mislead here (a naive
   "check the first 200KB of each 4MB stride" scan on this exact disc
   found the first real data ~250,000 sectors too late; re-scanning
   properly with `numpy.nonzero` over the full range found it immediately
   after a clean 2MB-aligned gap).
2. **Search first, scan second** (per `romhacking-community-tools-first.md`)
   — a raw-LBA archive scheme with no filesystem entry is exactly the kind
   of thing a preservation/romhacking community has already reverse
   engineered and published a standalone extractor for, especially for a
   commercially significant RPG. This is what cracked VP2: a plain
   WebSearch for the game's platform + "file format" + "QuickBMS"/"XeNTaX"
   surfaced a 2011 fan tool (`CUE`'s `triAce-PS2.c`) with the exact seed/
   algorithm/table-offset already solved, saving what would otherwise have
   been a much harder blind-decrypt effort. See the "search by magic bytes"
   addendum in `romhacking-community-tools-first.md` for the specific
   search tactic that worked here.
3. **Verify the found/derived table independently of "it looks plausible."**
   A wrongly-decoded LBA table won't survive: (a) a documented plaintext
   signature check at the table's own start, (b) adjacent-entry contiguity
   (`entries[i].lba + entries[i].sectors == entries[i+1].lba` holding with
   zero deviation across many pairs), and (c) summing every entry's byte
   size and comparing to the disc's total size — a correct table accounts
   for close to 100% of the disc (99.955% on VP2, with the last entry
   ending 2 sectors short of literal EOF); a wrong one won't.

## Why this generalizes beyond one title

The specific algorithm (XOR-scrambled LCG-style keystream) is tri-Ace-
specific and documented per-title in `game-re-corpora/valkyrie.md`/
`game-re-tooling/ps2.md` — but the *diagnostic* (near-empty ISO9660 tree +
huge disc size ⇒ check for a proprietary out-of-band archive before
assuming corruption) is a real pattern across multiple PS1/PS2-era Japanese
developers who prioritized load-time seek performance over standard
filesystem compliance, not unique to this one game or engine family.
