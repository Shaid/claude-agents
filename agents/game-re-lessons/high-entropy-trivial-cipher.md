# A file that "looks encrypted" (high entropy, or just zero readable strings) can be wrapped in a trivial cipher, not a dense one

**When it bites:** a file's entropy profile looks like dense compressed
data (~8 bits/byte) and you're about to reach for statistical
bitstream-cracking — **or** a save file/stat block has zero hits from a
plaintext string search despite an otherwise structured, low-entropy byte
layout (runs of `0x00`, "round"-looking values), tempting a "binary stat
block, no text fields" conclusion instead of checking for a cipher first.

FE2's savegames read as "3-byte magic + dense compressed bitstream" at
~8 bits/byte entropy. In reality it was 2 bytes of real magic + the first
*ciphertext* word (every file's plaintext happened to open with a small RLE
count, producing an illusory 3rd "magic" byte) — wrapping a near-trivial
zero-RLE compressor behind a self-keying cipher, where the key schedule
folds in plaintext, not ciphertext. Before assuming high entropy needs
statistical bitstream cracking, test plaintext-dependent/self-keying cipher
hypotheses, not just a fixed keystream.

**A near-zero-entropy variant of the same trap:** Wings (Amiga)'s
`pilot.dat` save file returned zero hits from `strings -n 3` despite
visibly *not* looking like dense random/compressed data (long `0x00` runs,
a handful of "round" byte values) — the natural read was "an opaque binary
stat-block format with no name/text fields," matching what a prior session
concluded. The real cause: every byte of the body is run through a
**single-bit rotation** (`ROR.B #1`/`ROL.B #1` per byte, applied a header-
supplied number of times) — trivial enough to leave `0x00` bytes and
low-order structure untouched (so the file doesn't read as high-entropy
at all) while still scrambling every ASCII byte in the name fields out of
the printable range. Tracing the save/load routine's disassembly located
the exact `ROR`/`ROL`-per-byte helper functions directly; applying the
inverse rotation and re-running a plaintext scan immediately surfaced 13
clean pilot names plus a working sum+XOR checksum, cracking the entire
record layout in minutes. **Lesson: "zero strings found" is not the same
signal as "high entropy" — both warrant the same first move (try a
trivial single-byte-transform cipher hypothesis, ROL/ROR/XOR/add-constant,
before assuming the format is opaque or that a stat block has no text
fields), and a save/settings file on any 1990s-era platform is a
plausible target for exactly this kind of throwaway obfuscation even when
it isn't "high entropy" in the traditional sense.**
