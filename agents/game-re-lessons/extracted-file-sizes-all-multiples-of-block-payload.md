# Every extracted file size a multiple of the block payload = the extractor is appending final-block padding

**When it bites:** a decoded/decompressed payload's size varies across a
corpus where it should be constant (portraits, fixed-size screens, a map
grid) — or you notice every *extracted* file's size is an exact multiple of
the container's per-block payload size (254 for C64 1541 chains, 128/512/2048
sectors, cluster sizes). Audit the extraction chain's final-block handling
before suspecting the codec or inventing a variable-size format.

Chained/block filesystems store the real length of the final block somewhere
a naive chain-walker ignores: a C64 1541 file chain's final sector reuses the
second link byte as the **offset of the last used byte** (not a sector
number); Amiga OFS data blocks carry a per-block data size; CP/M knows EOF
only to 128-byte records; FAT stores the byte-exact size in the directory
entry, not the cluster chain. An extractor that appends every block whole
hands each file up to `blockPayload − 1` bytes of stale tail garbage — which
a downstream RLE/LZ decoder happily consumes, turning constant-size payloads
into a spread of distinct sizes and disguising an extractor bug as a codec
mystery.

Confirmed on WIME C64 (`middilgard`): `follow_chain` in
`tools/wime/c64/extract-nib.py` appended all 254 data bytes of every final
sector. All 33 RLE-compressed PORT portraits "decompressed to 31 distinct
sizes, 5,022–5,260 bytes", the discrepancy was attributed to an RLE wrinkle
or a non-bitmap payload, and an escalation was framed at the codec layer. The
tell — **every extracted file's size was an exact multiple of 254** — pointed
two layers down. Honouring the final sector's byte count collapsed the
decompressed sizes to a constant 5,020/5,021 and, as a knock-on, corrected
the campaign map from "102×132" to 102×130 — identical to the CPC port's
grid; the "slightly different map resolutions between ports" claim was the
same padding. Full story: `middilgard/docs/wime/c64/engine.md` § Filesystem.

Cheap corpus test: `all(len(f) % blockPayload == 0 for f in extracted)` is
near-impossible for real variable-length content — if it holds, the extractor
is padding.

Sibling lesson: `padded-file-tail-describes-padding-not-content.md` covers
mastering padding present in the *stored* file; this one is padding your own
extractor introduces after the store was already byte-exact.
