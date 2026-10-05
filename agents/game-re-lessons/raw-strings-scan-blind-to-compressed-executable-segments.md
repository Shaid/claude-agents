# A `strings`/`grep` pass over a still-compressed executable container is blind, not evidence

**When it bites:** About to conclude "no literal string reference exists
anywhere in this executable" (e.g. to test a data-driven-vs-hardcoded
hypothesis) from a `strings -a`/`grep` pass run directly against the
on-disk executable file — especially a Switch `NSO0` (`main`/`subsdk*`),
or any other segment/block-compressed executable container (compressed
overlays, packed PE sections, etc.) — without first decompressing it.

## What happened

Testing whether four DLC characters' model filenames (`"UlysseA"`,
`"MC100"`, etc.) were hardcoded in FE Three Houses' `main` executable, the
first move was `strings -a -n 5 main | grep -i UlysseA` directly against
the raw on-disk exeFS file. Zero hits — for every single target string,
including generic ones expected to exist somewhere (`"action/model"`,
`".bin.gz"`). Taken at face value, this would have supported "definitely
not present" — but it would have been a coincidence of the *tool*, not a
finding about the *binary*: `main` is an `NSO0` container whose `.text`,
`.rodata`, and `.data` segments are normally **LZ4 block-compressed**
(no frame header, no checksum — see `game-re-tooling/switch.md`). A raw
byte scan of the compressed file finds only the handful of bytes that
happen to still look like printable ASCII inside compressed streams —
essentially nothing, regardless of what strings the *decompressed* image
actually contains.

The fix: run the project's own `buildNsoImage()` (or equivalent NSO
LZ4-block decompressor) to produce the full flat, decompressed image
first, *then* run the same string search against that. Only after
decompressing did real strings turn up at all (`"INFO0.bin"`,
`"DlcVersion.bin"`, a bare `"patch"` literal, etc.) — proving the
executable does contain meaningful ASCII content, just not the specific
target strings being tested for. The negative result for the *specific*
DLC character names held up after decompression too, but only the
decompressed-image search actually tested that hypothesis; the raw-file
search had tested nothing.

## The generalizable trap

A `strings`/`grep`/manual-hexdump scan of a container that is *known or
suspected* to compress its own segments/sections (NSO's LZ4 blocks, a
packed PE, a compressed ROM overlay) can return **zero hits for
everything** and this is completely uninformative — indistinguishable,
from the caller's side, from "the string genuinely isn't there." Before
trusting any string-absence result (or, symmetrically, being surprised a
string-presence hit didn't show up), confirm the region being scanned is
the *decompressed* view, not the raw on-disk bytes. This generalizes past
NSO to any platform where the executable container has a compression
flag per segment — check that flag (or just always decompress first) before
running any string-based hardcoded-vs-data-driven test.

The upside once you decompress correctly: a full whole-image byte-level
search (not a targeted symbol/xref search) for a small set of specific
literal name/path fragments is a fast, cheap, and — when it comes back
completely empty across the *entire* decompressed image (`.text` +
`.rodata` + `.data`, not just one segment) — decisive way to rule out
"hardcoded as a literal constant" before committing to expensive
full-binary Ghidra/radare2 disassembly. It only proves what it tests,
though: a zero-hit result rules out a *literal string* constant, not a
value built at runtime from smaller pieces (a hash, a template plus a
data-driven substring, character-by-character immediate construction).
