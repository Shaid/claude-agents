# Some background-graphics differences between language releases are real: painted-in signage, not misalignment

**When it bites:** comparing two language releases of the same console
game and a *graphics* resource family (tile pixel data, not text/font data)
shows a real, non-artifactual content difference concentrated in a small
subset of resources, while everything else in the same family is
byte-identical — before assuming the diff must be a decode bug, an
address-shift artifact (see
`fixed-offset-diff-across-builds-hides-pointer-shift.md`), or "graphics
never need localization."

Many SNES-era (and other console-era) localizations render town/location
signage, chapter titles, or similar short in-world labels as **hand-painted
pixel art baked directly into background tile graphics**, not through the
font/text engine — because the original artist drew a sign reading the
source-language place name directly into the tileset. A translated release
has to re-draw those specific tiles; everything else in the same graphics
family (which needs no such re-draw) stays untouched.

**Confirmed on FFVI (SNES), comparing the US and Japanese-original ROMs**
(`ceres` project): the field-map tile-graphics (`MapGfx`) and tile-formation
(`MapTileset`) resource families each showed a handful of resources with
real content differences — exactly 5/82 and 8/75 respectively — while every
other resource in both families was byte-identical. The differing
resources were, without exception, ones the reference disassembly project's
own file-naming convention already flagged with an `_en`/`_jp` suffix
(`narshe_ext_bg1_en`/`_jp`, `zozo_ext_1_en`/`_jp`, `vector_ext_en`/`_jp`,
`town_ext_*_en`/`_jp`, `destroyed_town_*_en`/`_jp`) — town/location name
signage painted into the tile graphics for Narshe, Zozo, Vector, and a
"destroyed town" cutscene backdrop.

**The check:** if a graphics-family diff between language releases isolates
to a small, specific subset of resources rather than showing either "zero
differences" (the strong default prior for pure pixel data) or "pervasive
differences shaped like a cascading address shift," check whether the
differing resources are specifically ones a player would see rendered with
visible in-world text (a shop sign, a town gate, a title card) — and check
whether a reference project's own asset catalog/naming already distinguishes
per-language variants for exactly those resources, which independently
corroborates the finding without needing to visually render and eyeball
the pixels yourself.
