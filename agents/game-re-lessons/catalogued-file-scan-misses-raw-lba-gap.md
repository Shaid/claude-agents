# A "scanned the whole archive, zero hits" negative only covers catalogued bytes — check for LBA gaps between files too

**When it bites:** a "scanned every catalogued file/archive entry for
format X, found zero hits, therefore the disc/game has no X" negative
claim, on a disc or archive that has **more than one** catalogued
container file — before trusting the negative, lay every catalogued file
out by its actual LBA/offset (not directory order) and check whether their
ranges cover 100% of the container. A healthy-looking, non-near-empty
catalogue can still hide a large raw, un-listed region between two
perfectly normal files.

This is a sibling trap to `iso9660-tree-near-empty-check-raw-lba-toc.md`,
not a duplicate of it — that lesson's trigger is a near-empty directory
tree (a handful of KB cataloguing a multi-GB disc). This one bites even
when the tree looks completely healthy. Confirmed on Chaos Legion (PS2,
Capcom, 2003, `~/Development/flower`): the ISO9660 tree has 22 real,
substantial catalogued files (a 403 MB flat asset archive, four ~54 MB
texture packs, the main ELF, IOP modules) — nothing about it looks
suspicious or near-empty. A first pass scanned every one of the 403 MB
archive's 3,024 catalogued entries for the MPEG Program Stream pack-header
marker (`00 00 01 BA`), found zero, and concluded the game ships no FMV at
all. Wrong: ~1.58 GiB of standard MPEG-2 Program Stream video (confirmed
via `ffprobe`+`ffmpeg`, a byte-exact 8-sector pack-stride invariant
independently corroborated by a literal `PROGRAM_END_CODE` landing exactly
where predicted, and three visually-confirmed decoded frames including the
game's own title/logo screen) was sitting in raw, un-listed sectors between
two ordinary catalogued files (`/MODULES/CAPSDRVD.IRX` and `/LEGION.IDX`) —
a gap invisible to any scan scoped to catalogued file contents, because it
was never a byte range any directory entry claimed.

**The fix, cheaply applied before trusting any archive-wide negative:**
`xorriso -indev <iso> -find / -exec report_lba --` (or equivalent) gives
every catalogued file's start LBA and sector count. Sort by LBA and diff
consecutive `start_lba[i+1]` against `end_lba[i] = start_lba[i] +
blocks[i]` — any gap means un-catalogued disc content exists, full stop,
regardless of how populated or reasonable the rest of the tree looks. Only
after confirming 100% LBA coverage (or explicitly characterizing every
gap — some are genuine zero-padding, verify with an exhaustive, not
sampled, non-zero byte scan) does a "zero hits across the whole archive"
result actually mean "zero hits on the whole disc."
