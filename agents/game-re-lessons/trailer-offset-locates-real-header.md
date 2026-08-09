# A container's real header can live at an offset given by the file's own last N bytes, not offset 0

**When it bites:** a family of same-purpose files (archive/resource
containers, one per "chapter"/"level"/asset-bank) shows no recognizable
magic or directory shape at offset 0 in any of them, sizes vary a lot, and
a magic-byte scan across the whole file also comes up empty or ambiguous —
before concluding the format needs a compressor identified or the magic is
simply unfamiliar, check the file's **last 4 (or 2) bytes** as a pointer.

Confirmed on Wings' (Cinemaware, Amiga) `.BOLT` container family: none of
the 11 shipped files' first bytes matched anything recognizable, and they
looked like raw payload data because they *are* raw payload data — the
real directory (ASCII magic `"BOLT"` + entry count + a 12-byte-stride
entry table) sits at an offset given by interpreting the file's **final 4
bytes** as a big-endian `u32`. Verified byte-exact across all 11 files (0
deviations: `byte[trailerOffset:trailerOffset+4] == "BOLT"` every time).
Code-confirmed too: the loader seeks to `filesize-4`, reads that value,
then seeks to it from the *start* and reads the "real" header from there —
a design that lets the file be extended (more payload prepended, directory
appended after) without moving anything already-loaded.

**Cheap test to run before deeper investigation**, on any unfamiliar
container whose offset-0 bytes don't resolve: read the last 4 bytes as a
big-endian (then little-endian) `u32` and check whether it's a plausible
in-bounds file offset (`0 <= v < filesize`) whose target bytes look like a
header (ASCII magic, small monotonic count field, etc.) — this is a
single-file, zero-cost check, cheaper than a compression-codec ID pass or
a structural/entropy scan of the whole file.

Generalizes: any format that needs to support streaming-append or
in-place-growth without relocating an existing header benefits from this
"trailer points at the real header" shape — don't assume "container" means
"header at offset 0" by default.
