# A familiar extension is not proof the file follows that format — or category — its name implies

**When it bites:** a file's extension matches a well-known format (`.LBM`, `.PCX`, `.BMP`, `.WAV`, `.MID`) or suggests a content category by convention (`.TIM` → texture), a doc already labels it so, and you are about to write a standard parser, reach for a sibling decoder, cite the format in a spec, or let a per-extension dispatcher skip or route the file — without having checked its magic.

An extension is a tooling convention (often the authoring tool's default, e.g. Deluxe Paint's `.LBM`), not a byte-layout guarantee. The worse form is a *wrong category*: a per-extension pipeline can exclude the file from every decoder silently, whereas a wrong format at least fails visibly. A palette-shaped run at offset 0 looks equally "right" with or without a `FORM` header, so a decode that skips to "palette starts here" can succeed on the wrong premise for a long time.

**Check / fix:** read the first 4–12 bytes (after decompression) and check the real magic — `FORM….ILBM`, `RIFF….WAVE`, `0x0A`+version (PCX), `BM` (BMP). In a mixed corpus, run one extension-agnostic classifier on decompressed magic and dispatch on that, in both directions (never "extension means skip", never "extension means format X"). Distinct from `renamed-magic-container.md` (magic deliberately swapped); for a numeric discriminant field matching an SDK enum see `pixel-format-value-guessed-from-enum-not-confirmed.md`.

**Canonical example:** Epic (Ocean, Amiga): every `.LBM` had been documented as IFF ILBM. A real chunk parser found no `FORM` in any of ~20 files; the content is `word[0]=0`, then 15–31 words all valid RGB4 (`<= 0x0FFF`), then raw bitmap — a custom `[16/32-entry palette][pixels]` layout.

**Variants:**
- *Wrong category* — NieR (PS3, `flower`): `.TIM` decompressed to `MTMI`, a fixed-stride table of animation-clip names; `recordCount*stride + header == fileSize` on 6/6 samples, no pixels.
- *Misleading extension, right family* — Reunion (Amiga AGA, `methanoid`): a `.BAT` in `sound/` is IFF `8SVX` after IMP! unwrap; `.RDA` is chunky `PBM `, not `ILBM`.
- *Category riding a well-attested container* — Eye of the Beholder II (Amiga, `crawl`): `TEXT.CPS`/`TEXT2.CPS`/`TEXT4.CPS` share `.CPS` with 100+ real LCW bitmaps but decompress to 22,463 bytes, md5-identical to the DOS port's `TEXT.DAT`.

**History:** 4 recorded instances (Epic, flower, methanoid, crawl) — full log in `_archive/familiar-extension-not-proof-of-standard-format.md`.
