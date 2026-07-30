# High whole-file entropy can mean a trivial compressor wrapped in a cipher, not a dense one

**When it bites:** a file's entropy profile looks like dense compressed data (~8 bits/byte) and you're about to reach for statistical bitstream-cracking.

FE2's savegames read as "3-byte magic + dense compressed bitstream" at
~8 bits/byte entropy. In reality it was 2 bytes of real magic + the first
*ciphertext* word (every file's plaintext happened to open with a small RLE
count, producing an illusory 3rd "magic" byte) — wrapping a near-trivial
zero-RLE compressor behind a self-keying cipher, where the key schedule
folds in plaintext, not ciphertext. Before assuming high entropy needs
statistical bitstream cracking, test plaintext-dependent/self-keying cipher
hypotheses, not just a fixed keystream.
