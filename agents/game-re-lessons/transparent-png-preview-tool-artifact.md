# A transparent PNG can look broken in an image-preview tool while being byte-correct

**When it bites:** a rendered sprite/font/tile atlas — especially large, or
with big background regions left fully transparent (alpha 0) — shows
implausible flat/solid colour blocks, an all-white or all-black wash, or
otherwise "wrong-looking" regions when viewed through an agent's inline
image-preview tool, right after writing a new PNG with `writePNG`/`Image`/
similar.

Some image-preview paths (large images especially) don't alpha-composite
transparency the way a real consumer would — they can render `alpha=0`
regions as an arbitrary flat colour, or downscale a large transparent PNG
in a way that produces blocky, solid-looking artifacts that aren't present
in the actual pixel data. Two confirmed instances on the same FFVI (SNES)
session (`ceres` project): (1) a 232-glyph font atlas rendered as pure
white-on-white in the preview (opaque white ink pixels over a fully
transparent background, composited by the preview against a white page —
correct data, misleading preview); (2) a 176-sprite monster/Esper graphics
atlas (1536x1920px) showed several cells as flat, garish solid-colour
blocks (green/blue/yellow squares) that looked like a decode bug — cropping
the same PNG with PIL and `Image.alpha_composite`-ing it over an explicit
opaque background (white or dark grey) showed every cell rendering
correctly; the "solid blocks" were a preview-tool rendering artifact on the
full, large transparent image, not present in the file's actual bytes.

**Before concluding a render is broken from an inline preview alone:**
crop the specific suspicious region and/or composite the PNG over an
explicit opaque background with PIL (`Image.alpha_composite(Image.new(
'RGBA', size, (bg,bg,bg,255)), img)`) before trusting a "this is wrong"
verdict enough to start debugging the decoder. This is cheap (a few lines
of Python) relative to the cost of chasing a decode bug that doesn't exist.
Conversely, once composited and still wrong, that's real signal — this
lesson is specifically about not skipping the composite-and-recheck step
before deciding.
