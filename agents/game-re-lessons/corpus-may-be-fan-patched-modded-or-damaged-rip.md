# The corpus may be fan-patched, modded or a damaged rip

**When it bites:** you model code or data from a dump whose filename carries a scene/fan tag (`[T-En by …]`, `Undub`, `Uncensored`, a version suffix). Or you find "three observed variants" of a routine that differ only in a jump to otherwise-unused space. Or a multi-disc set is assumed identical and read from Disc 1 only.

Fan translations hook the original code (often a `JMP` into padding) and rewrite tilemaps and text banks. Undubs swap audio banks. Bad rips zero-fill unreadable sectors and regenerate valid headers and EDC, so nothing at the disc layer flags them. A directory can also mix two builds (ECS and AGA level sets under one platform id). None of this shows up in a decoder. You end up modelling the patcher's code, or a hole in the rip, as the game's.

**Check / fix:**
- Read the dump's filenames and headers for group and version tags, and record provenance in the doc's inventory.
- Look for a **pristine copy** and diff sector by sector: a second track (CD audio-track sets can contain an unpatched data track), the other discs of a multi-disc set, an official re-release that embeds the original image (PSP/compilation bundles), or Redump hashes.
- Hash every file across all discs or copies. Any file that should be identical and isn't is either a known per-disc file or damage. Zero-filled whole-sector runs with valid sector headers point to a bad rip.
- Tag every extracted artifact `patched: true/false` (or re-extract from the pristine copy). Reclassify "variants" that exist only in the patched copy.
- Several build-tell signals in one directory (palette depth, source-path strings, which executable writes an AGA-only register) mean two builds. Split them by platform id.

**Canonical example:** Rondo of Blood (PC Engine CD). The project modelled Track 02, a fan-translated image. Track 22 equals the PSP re-release's `DRACX_02.DAT` on 9,997/10,000 sectors (the PSP blanked the boot sectors), while Track 02 differs on 1,661 sectors. The "three observed bank-B variants" were translation hooks: `$8267` reads `4C 00 9B` / `4C A0 93` / `4C 00 91` (jumps into `$FF` padding in the pristine image) where Track 22 and the PSP copy read `20 21 40`. About 20 native-model source files had been built on translation code.

**Variants:**
- Bravely Default (3DS): the dump is a fan "Undub v2.0 & Uncensored" build (`Sound.bcsar` is 0 bytes). Every byte-level and audio claim describes the mod.
- FF7 (PSX): a 3-disc md5 census found Disc 1's `TUNNEL_6.MIM` with bytes `0x10000–0x12FFF` all zero (6 whole sectors, valid headers and EDC). It decompressed to 211,351 B against 234,012 B on discs 2/3, and was the only file in the corpus with a distance-0 LZS reference. Take it from Disc 2.

Related: `partial-zero-fill-dropout-vs-corrupt-decode.md` (zero-fill runs behind a decode failure), `per-instance-file-set-may-be-duplicate-blobs.md` (hash the set), `cross-platform-decode-oracles.md` (re-releases as pristine copies).

**History:** 3 projects (Rondo of Blood, Bravely Default, FF7), plus one mixed-build directory (Alien Breed Tower Assault), 2026-11 audit sweep.
