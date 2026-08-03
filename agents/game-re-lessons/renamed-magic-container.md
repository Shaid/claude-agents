# A "custom" container may just be a public compressor with the magic renamed

**When it bites:** an unfamiliar 4-byte magic doesn't match anything you
recognize, the payload's compression pattern still "smells like" a known
Amiga/DOS-era codec (small header + efficiency/param bytes + a dense
bitstream), and you're about to start hand-disassembling a depacker or
statistically cracking the bitstream from scratch.

Jungle Strike AGA's `data/` files all start with `LR88` — not a magic any
tool recognized. Rather than disassembling the embedded depacker, the cheap
probe: copy one file, patch **only** bytes 0-3 from `LR88` to `PP20`, and run
`ancient identify`/`ancient decompress` (https://github.com/temisu/ancient,
supports dozens of retro compressors) on the copy. It immediately identified
"PP: PowerPacker" and decompressed byte-plausibly — the whole "custom" format
was vanilla PowerPacker with the studio's own build tooling swapping the
4-byte tag, probably just to stop naive players pointing stock unpacking
tools at their data. Confirmed empirically across the full 74-file corpus
(100% success, plausible ratios and structurally valid output), no
depacker disassembly needed.

General check, cheap enough to try **before** any hand-disassembly: if a
container's structure resembles a known format family but its magic doesn't
match, try patching just the magic bytes to each plausible real format's
magic (PP20/RNC1/RNC2/XPKF/ZOO...) and re-run `ancient identify`. A few
minutes of byte-patching can save a full depacker trace.
