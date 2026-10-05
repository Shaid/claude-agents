# A MAME `gfx_layout`'s `total` field can itself be a non-(1,1) `RGN_FRAC`, scaling the real tile count

**When it bites:** computing a MAME-driver gfx region's total tile count as
`region_bits / charIncrement` from a `gfx_layout` struct whose `total` field
is written as `RGN_FRAC(num,den)` — especially when every `gfx_layout` seen
so far in a project happened to use `RGN_FRAC(1,1)` for `total` (even while
using `RGN_FRAC(1,2)`/`(1,4)`/etc. for individual `planeoffset` entries in
the *same* struct), making the `num/den == 1` case look like the norm.

`src/emu/digfx.cpp`'s real resolution code (`IS_FRAC`/`FRAC_NUM`/
`FRAC_DEN`, read directly rather than assumed from the macro name) is:

```c
if (IS_FRAC(glcopy.total))
  glcopy.total = region_length / glcopy.charincrement * FRAC_NUM(glcopy.total) / FRAC_DEN(glcopy.total);
```

where `region_length = 8 * region_bytes` (bits, not bytes). When `total` is
`RGN_FRAC(1,1)` the trailing `* 1/1` is a no-op, so `region_bits /
charIncrement` alone happens to give the right answer — which is
indistinguishable, from the outside, from "the formula is just
`region_bits/charIncrement`, full stop." A `gfx_layout` whose `total` is
`RGN_FRAC(1,2)` (or any other fraction) needs the extra `* num/den` scaling
term, and skipping it silently **doubles** (or otherwise misscales) the
computed tile count — with no error, no exception, just a wrong total that
still looks plausible (the extra "tiles" past the real end decode as
garbage/noise, easy to write off as unremarkable atlas padding rather than
a sign the count itself is wrong).

Confirmed on Black Tiger (`kolbold`): `spritelayout`'s `total =
RGN_FRAC(1,2)` (shared by both the "tiles" and "sprites" GFXDECODE
entries), while every other `gfx_layout` this project had ported before
this session (`cps1_layout16x16`, `cps1_layout8x8`, `charlayout`) used
`RGN_FRAC(1,1)` for `total`. Naively porting the `region_bits/charIncrement`
formula from those earlier CPS1/CPS2 games gives 4096 tiles per 0x40000-byte
region; the real, source-derived count (with the `* 1/2` term applied) is
2048 — exactly half.

**The fix generalizes:** never assume a `gfx_layout`'s `total` field is
`RGN_FRAC(1,1)` just because every prior `gfx_layout` in the same project
happened to be. Read the struct's literal `total` field value from the
fetched driver source every time, and if it's a fraction other than `(1,1)`,
apply the full `region_bits/charIncrement * num/den` formula (ported
directly from `digfx.cpp`, not guessed from the macro's name) rather than
the simplified form that only coincidentally works for the `(1,1)` case.
