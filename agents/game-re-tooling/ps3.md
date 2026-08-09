# PS3 tooling notes

See `game-re-tooling/ghidra-loaders.md` for the Cell SPU processor module
(the PPU side is stock PowerPC).

## Retail game/DLC/patch PKG != Vita "finalized" PKG — don't trust `pkg2zip` blind

The obvious first tool for any PSN `.pkg` file is
[mmozeiko/pkg2zip](https://github.com/mmozeiko/pkg2zip) (MIT, portable C,
no dependencies). It is the right tool for **PS Vita** app/DLC/patch/PSM
packages and for PSX/PSP classics repackaged for Vita/Adrenaline — but it
**hard-rejects genuine retail PS3 game/DLC/patch packages** with
`ERROR: not a pkg file`. The cause is a real format difference, not a bug to
route around: `pkg2zip.c` requires a 64-byte Vita-only "finalized" extended
header (magic `eXt` / `0x7F657874`) at file offset `0xC0`
(`pkg2zip.c:339`'s `get32be(pkg_header + PKG_HEADER_SIZE) != 0x7F657874`
check). Classic PS3 packages don't have this block at all — their metadata
entries start directly at offset `0xC0`. Don't spend time patching or
debugging `pkg2zip` against a PS3 file; the underlying algorithm needed is
different (see below), and hand-implementing it is genuinely small (~150
lines).

Both header shapes share the same base 0xC0-byte layout up through
`data_offset`/`data_size`/`content_id`/`digest`/`pkg_data_riv` — reading
`pkg2zip.c`'s field offsets for that shared prefix is still valid and useful,
just don't rely on anything past it (its `items_offset` meta type=13 lookup,
`key_type` byte derivation, and the multi-key Vita/PSM key selection are all
Vita-only machinery that doesn't apply).

## Classic retail PS3 PKG decryption algorithm

Confirmed byte-exact on Drakengard 3 (main game + patch + all 18 DLC packs)
— full byte-level header table and verification evidence in
`docs/drakengard3/ps3/data-structure.md` in the `flower` project
(`game-re-corpora/flower.md`). Summary, since this generalizes to any
retail-PS3-PKG target:

- 192-byte (`0xC0`) fixed header, all fields **big-endian**. `data_offset`
  (u64 at 0x20) marks the start of the encrypted region; `pkg_data_riv`
  (16 bytes at 0x70) is the AES-CTR IV.
- **Single fixed AES-128 key for every retail PS3 title, no per-title
  derivation needed** (unlike Vita's zRIF/RIF): `2E7B71D7C9C9A14EA3221F188828B8F8`.
  Long public (originally documented at
  `wiki.henkaku.xyz/vita/Packages#AES_Keys`; also embedded, unused for this
  purpose, in `pkg2zip.c` as `pkg_ps3_key`).
- AES-CTR convention: treat `pkg_data_riv` as a big-endian 128-bit *initial
  counter*; to decrypt `size` bytes at region-relative byte offset `rel_off`,
  use `counter = pkg_data_riv_as_int + rel_off/16` (16-byte AES blocks).
  Apply independently to the item table, each item's name, and each item's
  file data at their own respective offsets — don't decrypt the whole
  encrypted region as one continuous CTR stream, each sub-region restarts
  its own counter from its own offset.
- Item table: `item_count` fixed 32-byte records starting **immediately** at
  `data_offset` (no separate `items_offset` indirection — that's a
  Vita-specific meta type=13 block that doesn't exist here).
- No PS3-specific tool build was needed once the algorithm was known — a
  from-scratch implementation in ~150 lines worked first try in both Python
  (`cryptography` package — not `pycryptodome`, which wasn't preinstalled —
  `cryptography.hazmat.primitives.ciphers`) and Node (built-in `crypto`
  module's `'aes-128-ctr'` cipher + built-in `zlib`, no npm dependency).

**Cheap ground-truth oracles for verifying a PS3 PKG decrypt**, before
touching any game-specific asset format: `PARAM.SFO` must start
`00 50 53 46` (`\x00PSF`), `ICON0.PNG`/any `.PNG` must start with the
standard PNG signature, a PS3 trophy `.TRP` file must start `DC A2 4D 00`
(`0xDCA24D00`), a Bink video `.BIK` must start `BIKi`/`BIKb`/`BIKd`/`BIKf`/
`BIKg`. All four matched exactly on the first attempt once the decrypt
algorithm above was implemented — a fast, free multi-file confirmation
before spending time on anything asset-specific.

## `EBOOT.BIN` / SELF (not solved, noted for future reference)

Any file with flag byte `0x01`/magic `SCE\0` is a SELF-signed ELF — a
separate NPDRM code-signing layer on top of the outer PKG encryption above.
Out of scope unless the goal is code, not data. RPCS3's
`Crypto/unself.cpp` (GPLv2) would be the reference to start from, by
analogy with the `.EDAT` work below (same repo, same NPDRM key family).

## NPDRM `.EDAT` decryption, given a `.rap` license file

`.EDAT` files (magic `NPD\0`) are NPDRM-wrapped. Unwrapping needs additional
per-title key material beyond the outer PKG's fixed key — specifically a
**RAP file** (a 16-byte binary license, named `<content_id>.rap`, one per
purchasable content id — main game, each DLC pack, etc.). Confirmed working
end-to-end (byte-exact, cross-verified between an independent Python probe
and a committed, tested TypeScript module — `tools/shared/ps3-edat.ts` in
the `flower` project) once RAP files were supplied. **Don't treat a missing
RAP as a hard blocker without asking** — it's exactly the kind of
"ground truth cannot be obtained any other way" situation the autonomy
contract calls out; the user may have them and not think to mention it
until asked, as happened here.

Algorithm, reconstructed from RPCS3's `Crypto/unedat.cpp` (GPLv2 — read for
reference, reimplemented from scratch, not copied) plus the
publicly-documented RAP→klicensee transform in
`windsurfer1122/flatz-rif-rap-converters`'s `rap2rif.c`:

1. **RAP → klicensee**: AES-128-ECB-**decrypt** the 16-byte RAP with a fixed
   public key (`RAP_KEY = 869F7745C13FD890CCF29188E3CC3EDF`), then apply 5
   rounds of a XOR/permute/subtract scramble using three more fixed public
   16-byte tables (`RAP_PBOX`, `RAP_E1`, `RAP_E2` — see `key_vault.h` in
   RPCS3, or `tools/shared/ps3-edat.ts`'s `rapToKlicensee` for the exact
   byte-level transform). No per-console material needed — this is the
   NPDRM-license-only "klicensee," distinct from the full device-activated
   "RIF" a real PS3 would build from it plus `act.dat`; klicensee alone is
   sufficient for offline decryption.
2. **Container layout**: `NPD_HEADER` (0x80 bytes: magic, version, license
   type, content_id[0x30], digest[0x10], title_hash[0x10], dev_hash[0x10],
   activate/expire times) + `EDAT_HEADER` (0x10 bytes: flags, block_size,
   file_size), then reserved bytes up to offset `0x100`, then per-block
   metadata + AES-CBC-encrypted data blocks.
3. **Per-block key derivation**: `block_key = dev_hash[0:12] + BE(block_num)`,
   `key_result = AES-ECB-encrypt(klicensee, block_key)`. If
   `EDAT_ENCRYPTED_KEY_FLAG` (`0x8`) is set in the header's flags (it was,
   on every `.EDAT` found in the one title tried so far — flags `0x3C`),
   one more step: `key_final = AES-CBC-decrypt(EDAT_KEY_1, zero_iv,
   key_result)` using another fixed constant
   (`EDAT_KEY_1 = 4CA9C14B01C95309969BEC68AA0BC081`). Then
   `plaintext_block = AES-CBC-decrypt(key_final, npd.digest, ciphertext_block)`.
   Hash/CMAC verification of each block can be skipped entirely if the goal
   is just recovering plaintext (RPCS3 itself notes this check is too slow
   to bother with) — verify correctness structurally instead (magic bytes,
   or byte-diff against an independently-obtained plaintext copy of the
   same logical file, if one exists on another release/SKU/disc).
4. `metadata_section_size` and per-block data offset depend on which of
   several `EDAT_HEADER.flags` bits are set (`EDAT_COMPRESSED_FLAG`,
   `EDAT_FLAG_0x20` for per-block-preceding metadata, `EDAT_DEBUG_DATA_FLAG`)
   — see `unedat.cpp`'s `decrypt_block()` for the branches; only the
   "flags `0x3C`, NPD version 4" shape has been exercised/confirmed so far.

**A `.EDAT` filename suffix does not imply the file is bulk content** — in
the one title checked so far, every `.EDAT` was a tiny (hundreds of bytes,
sometimes literally zero-byte-payload) DRM entitlement marker, and the
*real* bulk asset content shipped as ordinary unwrapped files right next to
it. Don't assume `.EDAT` is blocking meaningful extraction without actually
decrypting one and checking its declared `file_size` first.

## Static recompilation (native-port stretch goal)

See the "Recompilation landscape" table in `game-re.md` — `docs/ps3-recomp.md`
in `seer` is the platform's entry there.
