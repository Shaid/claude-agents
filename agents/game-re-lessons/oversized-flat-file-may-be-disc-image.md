# An oversized "data file" with no container match may be a mounted disc image

**When it bites:** a single named data file (e.g. `GAME.DAT`) is orders of
magnitude larger than every other file in the corpus, its size doesn't line
up with anything the game's strings/executables suggest, and a known
container parser (PAK/archive directory) rejects its header as corrupt in
both endiannesses.

Lands of Lore's `data/landsoflore/dosvga/GAME.DAT` is 306,751,488 bytes —
next to a folder of otherwise-small files (`.ADL` music tracks, a few KB
each; `manual.pdf`). It doesn't parse as the Kyra engine's PAK container
(`ResLoaderPak`'s directory-offset bounds check fails both little- and
big-endian). Checking byte offset `0x8001` for the ASCII string `CD001`
(the ISO 9660 Primary Volume Descriptor signature, always at sector 16 of
a 2048-byte-sector image) confirmed it instantly: the file is a raw CD-ROM
disc image, not a Kyra resource — a modern repackager (GOG-style) had
mounted the original install CD and dumped it verbatim under a filename
that looks like ordinary game data. `7z l`/`7z x` read ISO 9660 natively
and immediately exposed the real directory tree (`DATA/STARTUP.PAK`,
`DATA/ENG/GENERAL.PAK`, dozens of per-level PAKs) — the actual Kyra files
the container parser was looking for all along, just one layer deeper.

General check, cheap enough to try before assuming a file is corrupt or a
custom format: if a file's size is wildly disproportionate to its siblings
and a plausible container parse fails cleanly (bounds-checked rejection,
not garbage output), check for a disc-image signature — ISO 9660's `CD001`
at `0x8001` (or `0x8801`/`0x9001` for other sector sizes), or a BIN/CUE
pair's sync pattern — before spending time on the file's presumed native
format. `7z` reads ISO 9660 (and several other disc-image formats)
out of the box with no extra tooling; extract to a scratch/cache directory
if the source tree is read-only, since the "real" files are the payload,
not the ISO wrapper itself.
