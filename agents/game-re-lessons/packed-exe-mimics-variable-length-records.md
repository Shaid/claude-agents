# A packed executable can fake a variable-length record format

**When it bites:** a byte-pattern census against a DOS-era (or other packed-
capable) executable's raw file bytes finds what looks like a genuine
variable-length record format — some records shorter than others, in
distinct length classes, with a "residue" of a few extra bytes near the
boundary that resists every attempt to map to a plausible field — especially
if record boundaries themselves (found via some other independent anchor,
like a string/name-pointer scan) look completely solid.

**Check whether the executable is packed *before* modelling any record
encoding from raw file bytes.** A packer's own run-length/fill-run
compression can shrink a genuinely fixed-stride record whenever it contains
a run of a repeated byte (most commonly a run of zeros — a null
position/pointer/flag field, which is disproportionately common exactly on
the "special-case" records that most invite a variable-length theory in the
first place). Reading the packed bytes directly then makes those records
look shorter, and the compressor's own command/length/fill operand bytes —
sitting right where the "missing" field used to be — look like a
plausible-but-stubborn data field. Confirmed on War in Middle Earth's DOS
VGA `START.EXE`: two full sessions modelled a "30 of 196 entity records are
a shorter, non-standard shape" theory (one session even found a partially-
correct-looking "magnitude-dependent field width" rule that fit 30/30 cases
for the wrong reason) before discovering the file is Microsoft EXEPACK-
compressed. Once unpacked, the entity table was a plain uniform 37-byte
stride with zero exceptions; the "residue bytes" were EXEPACK's own
`0xB0`–`0xB3` command bytes plus their length/fill operands, and `FLAG +
apparentRecordLength` was constant across every "short" record precisely
because it was reconstructing the packer's own fixed 44-byte scratch chunk,
not because of any relationship in the game's data model.

**Cheap checks, in order of cost:**
1. MZ header: `NumRelocs == 0` is the standard symptom (a packed image's
   real relocations live *inside* the packed data, applied by the unpacker
   stub at load time — the outer MZ header legitimately has none of its own).
2. Search the file for a packer's canonical error string — Microsoft
   EXEPACK ships the literal ASCII string `"Packed file is corrupt"`;
   LZEXE has its own tag (`LZ91`, see `cross-platform-decode-oracles.md`).
   `strings -a` the file; this costs seconds.
3. For EXEPACK specifically: an 18-byte header sitting immediately after
   the packed image, at the entry point's own `CS:0000`, ending in the
   signature word `0x4252` ("RB").
4. **A derived segment base that isn't paragraph-aligned is proof the
   offsets in use are wrong**, independent of the above — a real x86 real-
   mode segment base is always a multiple of 16 (`dsBase mod 16 == 0`). If a
   `DS_BASE` derived by cross-referencing a known string lands on, say,
   `...C74` instead of `...720`, that's a free, structural signal to go
   looking for a packed-file-vs-real-image offset mismatch before trusting
   any table built on it.

**If a census finds a suspicious recurring byte motif that resists every
per-record field interpretation, re-run the same census file-wide, not just
within the suspected data region.** The motif recurring inside obviously
non-data contexts — between function epilogues and prologues, right after
`$`-terminated DOS strings, anywhere code unambiguously lives — is decisive
proof it isn't content at all, and is what actually cracked this case (a
`re-codebreaker` escalation found the motif recurring 107 times file-wide
before ever identifying it as an EXEPACK command). A census scoped only to
the region under suspicion can never produce this negative result, no
matter how long you stare at it.

See also `cross-platform-decode-oracles.md`, which covers the sibling
failure mode: a known-content *search* against a packed executable finding
nothing (a false negative) rather than this lesson's false positive
(fabricating structure that isn't there).
