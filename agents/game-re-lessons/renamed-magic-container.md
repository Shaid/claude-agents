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

**Second variant: the whole header is XOR-obfuscated, not just the magic
substituted.** Embryo (Beyond Arts, Amiga, 1994)'s data files all showed
magic `"PaCk"`/`"Pack"` — not a simple renamed tag this time, since a plain
substitution-only guess against known magics found nothing. Disassembling
the loader's own file-read routine showed it XORs the first 14 header bytes
with 4 fixed 68k `EORI` immediates (`0x13132e59` over the magic longword,
`0xfacd`/`0xdeadface`/`0xfadeabcd` over the following fields) before using
them — `0x5061436b ^ 0x13132e59 = 0x43724d32` ("CrM2"), i.e. genuine
Crunch-Mania, just obfuscated by XOR rather than renamed by substitution.
Same fix as above once you know the mask: de-XOR a copy's header, leave the
payload untouched, and `ancient identify`/`decompress` confirms it
independently (114/115 files, 0 deviations, byte-exact decompressed-length
match against the game's own header field). If a magic doesn't match any
known format even after trying substitutions, and the file is small enough
to disassemble, check the loader's own magic-comparison code before
assuming the format is genuinely custom — a `CMPI.L #$imm,Dn` immediately
following a length/magic read is the tell, and the immediate operand (or an
`EORI`/`EOR` applied to the buffer just before the compare) hands you the
transform directly, cheaper than statistically guessing at one.
