# A material can name a colour texture it doesn't embed — the real map lives in a separate texture-only file

**When it bites:** a model has UVs and a multi-mapper material, the export binds whichever texture the model file happens to embed, and the render comes out near-black, flat or "chrome". Only one mapper resolves locally (often a small environment/reflection map); the others name textures that are nowhere in the file.

**The trap:** treating "first embedded texture" as the colour map, or concluding the model has no colour texture because none is embedded. The material's other mappers *name* the real colour/specular maps, which ship in companion texture-only containers (no models inside) and are picked per unit/costume by a separate table. The companion file often stores the texture under the *base* name even when the file itself is a variant (`*_c1` file holding a texture named `*_c0`), so a filename-only match misses it.

**Check / fix:**
- Dump every mapper's texture **name** and role, not just the ones that resolve to embedded data. An unresolved name is a lead, not noise.
- Census the corpus for texture-only containers (files that parse as the texture/model format but carry zero meshes) and index them by the internal texture name, not the filename.
- Find the table that picks the variant file per unit (class preset, palette/costume slot, appearance data) rather than guessing `_c0`.
- Prove the binding: name-match count over all parts **plus a wrong-unit null** (another unit's name should match ~0). A UV-seam colour-continuity score, right texture vs a plausible wrong one, is an independent check.
- Related: when the material does reference an *embedded* texture, pick it by the binding table, not by size — `embedded-texture-size-does-not-predict-material-diffuse-binding.md`.

**Canonical example:** Fire Emblem Awakening (3DS, CGFX battle models, `lucina`). Mapper 0 is an embedded 128² `envmap`; mappers 1–2 name `<unit>_c0` / `_s0`, which are not in the model file. The colour maps come from 687 texture-only `b/<variant>.t.lz` files chosen by the class preset. The material names the unit's `_c0` in 187/187 parts vs 0/187 for another unit's name; seam error is lower for the right texture than the other gender's in 84/91 bodies. Detail: lucina `docs/3ds-formats.md` §11.4.

**History:** 1 instance (lucina, 2026-11).
