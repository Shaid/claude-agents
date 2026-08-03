# A library-call opcode byte pattern isn't proof of which library it calls

**When it bites:** you've searched a 68k binary for a specific LVO call by
its raw opcode bytes (`4EAE` + a 16-bit negative displacement, e.g. `4EAE
FF3A` for graphics.library's `OpenScreen` at LVO `-0xC6`) to census every
real call site of that function — especially when trying to prove a
negative ("is there a second/alternate palette-load or screen-open site
anywhere in this binary?").

Different AmigaOS libraries assign the same negative LVO displacement to
completely different functions — the opcode bytes for `JSR -0xC6(A6)` are
identical whether `A6` holds `GfxBase` (→ `OpenScreen`) or some other
library's base (→ whatever that library put at offset `-0xC6`). A raw byte
search for `4EAE FF3A` across a 351KB CODE hunk returned 4 hits; only 1 was
a real `OpenScreen` call. The other 3 loaded `A6` from a fixed global
already confirmed (by tracing the immediately-preceding `OpenLibrary` call
sequence) to be `SysBase`/`ExecBase`, not the `GfxBase` pointer stored
after a successful `OpenLibrary("graphics.library")` — so at those 3 sites
`-0xC6(A6)` calls a *different* library's LVO that happens to share the
displacement, not `OpenScreen`.

**Fix:** never trust an LVO opcode match alone. For each hit, walk backward
to the nearest `MOVEA.L <src>,A6` (or equivalent) and confirm `<src>` is
the specific library-base global you've already independently confirmed
(e.g. via tracing the matching `OpenLibrary("name.library")` call and where
its return value gets stored). Only count hits whose `A6` provenance
matches. This is what let one session confirm, by exhaustive census rather
than more rendering guesses, that a 351KB binary has exactly ONE real
`OpenScreen` + ONE real `LoadRGB4` call in its entirety — settling "does
this other asset class load a different palette?" structurally instead of
leaving it as an open rendering question (Wizardry 6 Amiga, `sorcery`
project, `.EGA` full-screen images turned out to share the game's single
screen/palette with its `.PIC` cels).
