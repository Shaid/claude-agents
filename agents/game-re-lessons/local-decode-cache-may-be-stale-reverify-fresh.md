# A project's own `build/cache/` decode artifact from an earlier session may be stale or wrong-length — re-decode fresh from the raw disc/ROM before trusting it for a byte-exact claim

**When it bites:** you're about to disassemble, byte-diff, or cite a
specific offset in a cached decompressed/decoded artifact under
`build/cache/<game>/` that an earlier session produced — especially a
small, rarely-touched file (a short overlay, a small sub-module, a header
fragment) rather than one of the project's large, frequently-regenerated
main assets. The cache directory is convenient (no need to re-run the
decompressor) but nothing enforces that it still matches what a fresh
decode of the current raw disc/ROM files would produce.

## What went wrong (and the check that caught it)

On Valkyrie Profile (PSX, `valkyrie` project), a corpus-wide sweep for a
companion-array address idiom found a hit inside `codeoverlay_slot2293.bin`
in the project's own `build/cache/`. That cache file was 22,528 bytes for
disc 1 but only 2,944 bytes for disc 2 — a discrepancy an earlier session
had already partially investigated and explained away as "disc2's own
cache is a truncated prefix" (i.e., blamed the *smaller* file as
incomplete). Re-decoding the TOC slot fresh from both discs' raw bytes (not
from either cache file) showed the opposite was true: the real decompressed
content is 2,944 bytes on **both** discs, byte-identical. The disc1 cache
file — the one nobody had doubted — was the stale/wrong one, presumably
left over from a different extraction attempt or a bug in whatever probe
first wrote it. Trusting the disc1 cache at face value would have meant
disassembling ~19,500 bytes of content that don't belong to this TOC slot
at all, and could easily have produced a plausible-looking but entirely
spurious "hit" past the real end of the resource.

## Fix

Before citing an address/offset inside a cached decode artifact as part of
a byte-exact verification claim, re-decode the same resource fresh from
the project's raw disc/ROM files (the same TOC/directory read + decompress
call the cache itself was presumably built from) and diff the two. Do this
for **both** discs/regions independently — don't assume one is the honest
baseline just because it's larger, newer, or was the one an earlier
session already flagged as suspicious; check the one nobody doubted too.
A cheap, decisive tell that something is off: two same-named cache files
for what should be byte-identical disc1/disc2 content (a common convention
for shared code overlays) have different lengths at all — that alone is
worth a fresh re-decode before either is trusted, regardless of which one
looks more "complete."

This risk isn't limited to throwaway probes reading a cache file once —
it can be baked permanently into a *committed* verify script that never
re-derives from the disc at all, and that class of violation is
grep-discoverable in bulk across a whole project's `verify-*.ts` corpus,
not just one file at a time. See `tracker-prose-is-not-evidence.md`'s
eleventh variant for the citation-chain shape this takes between sibling
scripts and the sweep technique that finds a pool of instances at once.
