# Nintendo Switch tooling

Read before working any Switch target (`~/Development/chimera` is the
account's Switch project — Astral Chain, FE Three Houses, FE Warriors, FE
Engage, FE Warriors: Three Hopes).

## Getting at the data: `hactool`, and the partition everyone forgets

`chimera` vendors a working binary at `tools/.bin/hactool`, driven by
`tools/extract-romfs.ts`. Keyset lives at
`~/Development/switch-prod-keys/Keys-17.0.0/prod.keys`.

```
tools/.bin/hactool -k <prod.keys> --disablekeywarns -i <NCA>            # info
tools/.bin/hactool -k <prod.keys> --disablekeywarns --listromfs <NCA>   # dir listing, no extraction
tools/.bin/hactool -k <prod.keys> --disablekeywarns -x --romfsdir=<out> <NCA>
tools/.bin/hactool -k <prod.keys> --disablekeywarns -x --exefsdir=<out> <NCA>
```

Caveats learned the hard way:

- **hactool 1.4.0 chokes on keysets with over-long lines.** A v22.1.0
  keyset's `eticket_rsa_keypair` overflows its 1024-byte line buffer. Use a
  v17.0.0 keyset.
- **PFS0 entry offsets are relative to the file-data base**, not the file
  start: add `0x10 + entryCount*0x18 + stringTableSize`. Reading at the raw
  offset lands on `cnmt.xml` instead of the NCA.
- **`hactool` invoked via a captured Node pipe (`execFileSync(..., {encoding: 'utf8'})`) can fail outright — `ENOBUFS`, not Node's own `ERR_CHILD_PROCESS_STDOUT_MAXBUFFER` — on a title with a very large RomFS.** Confirmed reproducibly (2/2 attempts) on FE Engage (`chimera`): `--listromfs` on a title with ~180K files produces enough stdout that this sandboxed environment's synchronous pipe capture fails, even though the same command works fine on every smaller title `tools/extract-romfs.ts` was originally written against. Fix generically, not per-title: write `hactool`'s stdout to a real temp file (`execFileSync(HACTOOL, args, {stdio: ['ignore', fd, 'ignore']})` against an `fs.openSync`'d path) and read it back, instead of capturing through a pipe at all. Any tool wrapper that shells out to a CLI expected to print a large listing (a full RomFS file dump, a large disassembly, a big log) on a big-corpus title should default to this pattern rather than a captured pipe.
- **A one-shot RomFS extraction can silently drop whole directories.**
  Confirmed twice in `chimera` (Three Houses lost `nx/sound/`; FE Warriors
  lost eight directories including `nx/sound`+`nx/voice`, and a "no audio in
  this game" verdict shipped in the docs before it was caught). Always
  compare `--listromfs`'s file count against the extracted tree's real count
  before drawing *any* conclusion from an absence.
- **Extract the ExeFS too, always.** It is a few MB next to a 14 GB RomFS
  and it is where a title's resource-ID→filename tables live. See below;
  see also `executable-resource-path-registry-names-asset-ids.md`.
- Patch (BKTR) NCAs need `--basenca` plus a title key. Update NSPs are
  otherwise skipped, which means "asset type X doesn't exist" claims must
  state whether the update was checked.
- **DLC/AddOnContent NSPs use the same Rights-ID (title-key) crypto as BKTR
  update patches, but are NOT Patch/BKTR partitions** — no `--basenca`
  needed, they're a normal small self-contained RomFS. `hactool -i` on the
  raw carved NCA reports `Titlekey: Unknown`/`Content Type: PublicData`
  until `--titlekey=<hex>` (looked up in `title.keys` by the NCA's own
  declared Rights ID) is supplied. A largest-NSP/largest-NCA-only
  extractor (a common, reasonable default for grabbing just the base
  Program NCA) silently never touches DLC NSPs at all — no error, no log
  line — since they're routinely tens of MB against an 11+ GB base game.
  Confirmed real, previously-undocumented paid content hiding exactly
  there on Fire Emblem: Three Houses: 2 of 12 DLC NSPs held cosmetic 3D
  outfit geometry in their own small, separate `DATA0.bin`/`DATA1.bin`
  pair. Before any "content X doesn't exist" write-up, `find data
  -iname '*.nsp'` and check the extraction pipeline actually covers every
  hit, not just the base game — see
  `content-type-absence-needs-multiple-independent-angles.md`'s "Angle 6".

## `NSO0` executables (`main`, `subsdk*`, `rtld`, `sdk`)

ExeFS modules are `NSO0` containers whose three segments are normally
**LZ4 *block*** compressed (no frame header, no checksum). Layout, all
little-endian:

| Offset | Size | Field |
|---|---|---|
| `0x00` | 4 | magic `"NSO0"` |
| `0x0c` | 4 | flags — bit 0/1/2 set = text/rodata/data segment compressed |
| `0x10`/`0x20`/`0x30` | 16 each | `u32 fileOffset, u32 memoryOffset, u32 decompressedSize` (+4 unused) |
| `0x3c` | 4 | `.bss` size |
| `0x60` | 12 | `u32 compressedSize[3]` |

Lay each segment out at its `memoryOffset` in one zero-filled buffer sized
to cover the last segment plus `.bss`; virtual addresses read out of the
module's own pointers then index that buffer directly. (`.text` at vaddr 0
is common, making the mapping the identity — don't hardcode that.)

**Every segment must expand to exactly its declared `decompressedSize`.**
That is a zero-deviation invariant across all three and doubles as your
decompressor's correctness check — assert it rather than trimming.

**Apply the NSO's own relocations before disassembling code, or every
GOT-indirect global load reads as zero and looks like a dead end.**
`buildNsoImage()` only lays segments out at their declared virtual
addresses — it does not apply the image's dynamic relocations. An
`adrp`+`ldr` sequence loading a global through the GOT then reads whatever
raw byte the linker left there (typically `0`), which reads as "opaque/
unresolvable global" rather than a missing processing step. Fix: `MOD0` at
**file offset `0x8`** (a self-relative `i32`) locates a small header giving
`.dynamic`'s address; read `DT_RELA`/`DT_RELASZ`/`DT_RELACOUNT` from it and
apply every `R_AARCH64_RELATIVE` entry (`*(image + r_offset) = imageBase +
r_addend`) into the flat image before trusting any loaded global's value —
on FE3H's `main` this was 71,869 entries and unblocked every previously
opaque GOT-indirect load project-wide. The same `.dynamic` walk finds a
real `.dynsym`/`.dynstr`, letting `R_AARCH64_JUMP_SLOT` PLT entries name
imports (`malloc`, `nnMain`, engine entry points, …) directly — a much
stronger oracle than guessing a function's role from call shape alone. See
`unrelocated-nso-elf-got-load-reads-as-zero.md` for a worked failure this
exact gap caused (two independent disassembly passes over the same
unrelocated image both misidentified the same two functions).

**Never run `strings`/`grep` against the raw on-disk `main` file to test
"does this literal exist in the executable."** With any compression flag
set (the common case), that scans compressed bytes and returns near-zero
hits regardless of what the decompressed image actually contains — a
false negative, not evidence of absence. Decompress via `buildNsoImage()`
first, then search the flat image. See
`raw-strings-scan-blind-to-compressed-executable-segments.md`.

Reference implementation: `chimera`'s `src/data/formats/nso.ts` (NSO parse +
a ~30-line hand-written LZ4 block decoder — no dependency needed; `python3
-m pip install lz4` is blocked by PEP 668 on this machine anyway, and the
naive bulk-copy port of an LZ4 match is wrong because overlapping matches
are legal and common).

## The resource-path registry (Koei Tecmo, loose-file titles)

FE Warriors' `main` carries a flat 13,133-entry array of
`{u64 pathPtr, u64 handleSlotPtr, u64 flags}` naming every loadable file in
numeric-resource-ID order — the complete ID→name oracle for its gamedata
tables, and the only one that exists for that game. `chimera`'s
`src/data/formats/kt-resource-registry.ts` locates and parses it.

**Whether a title has one is predicted by its container design**, so check
this before hunting:

- **Loose files in the RomFS** (FE Warriors: no LINKDATA at all) → the
  executable must hold literal paths. Expect a registry.
- **Indexed archives** (Three Houses' `DATA0`/`DATA1`, Three Hopes'
  `LINKDATA`) → assets are addressed by number; the executable holds only
  `"%s.bin"`/`"%s:/%s.bin"` templates. Both were checked: **no registry**.

The locator's signature is the `handleSlotPtr` advancing by exactly 8 per
entry with `flags` constant — but that alone false-positives on both
archive-indexed siblings (17,322 and 946 bogus entries respectively), so it
must also score candidate runs on whether the pointers resolve to
path-shaped strings. See
`pointer-array-stride-signature-needs-content-plausibility.md`.

## Other Switch notes

- Tegra textures are GOB block-linear swizzled; a block-compressed (BC/ASTC)
  surface must be deswizzled at its real block size, not bpp=1/1×1 — see
  `byte-granular-deswizzle-of-block-compressed-data.md`.
- **An update's romfs is a LayeredFS tree (`patch1/`, `patch2/`, … — higher
  layer wins) and its loose files override the base game's archives.** So a
  table packed inside a base archive routinely reappears as a plain named
  file in a patch layer, often with *more content* (DLC records the base
  build leaves all-zero) and sometimes in a **revised struct**. Two things
  follow: never call an asset type absent until the update dumps have been
  decrypted and checked too, and when a base-game table won't decode, look
  for the patch layers' copy before starting any byte-census — see
  `update-patch-ships-a-revised-struct.md` (FE3H's `Scenario` was solved this
  way after two passes on the base file alone had stalled).
- Ghidra has a Switch loader; see `game-re-tooling/ghidra-loaders.md`.
- For code analysis on a decompressed NSO image, remember `.text` is
  AArch64 and the image you built above is already the correct memory
  layout — feed the flat image, not the `NSO0` file, to a raw-binary import.
- **Cheap alternative to a full Ghidra/`aaa` pass for "is this rodata string
  load-bearing or dead debug text": hand-decode `ADRP`+`ADD` pairs.** Since
  the decompressed image already has vaddr == file offset, a ~40-line Python
  scanner over every 4-byte-aligned word in `.text` finds real string xrefs
  in seconds: decode `ADRP`'s page target as `(pc & ~0xFFF) + (imm21 << 12)`
  (`imm21` = sign-extended `immhi:immlo`, bits `[23:5]:[30:29]`), collect
  every `ADRP` whose page matches your target string's page, then check the
  next instruction for an `ADD (immediate)` on the same destination register
  whose 12-bit immediate equals the string's low-12 offset. A page holds many
  strings, so most `ADRP` hits to the right page are false; the following
  `ADD`'s exact low-12 match is what confirms a specific string. Confirmed on
  FE Three Houses' `main`: found 9 real call sites for one shader-parameter
  name in under a minute, no Ghidra load needed — and an *interleaved*
  call-site pattern between two different named constants (alternating in
  the same code region) was itself decisive evidence of a shared
  name-registration loop, without disassembling a single instruction by
  hand. Limitation: only catches the 2-instruction-adjacent form — a value
  loaded via a longer sequence (register copy, precomputed pointer table)
  needs a real disassembler.
