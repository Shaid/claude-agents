# A decoded, already-classified byte blob may be an image nobody tried rendering yet

**When it bites:** hunting for a visual/renderable asset format, and the
search keeps circling unexplored territory (unclassified files, un-decoded
containers, un-cracked compression) while a *different*, already-decoded,
already-named bucket of bytes sits nearby with a semantic hypothesis
attached (built from indirect evidence — a magic tag's name, co-located
metadata, a plausible-sounding guess) that was never actually tested by the
cheapest possible check: does it just render as pixels.

Confirmed on Valkyrie Profile 2: Silmeria (PS2, `~/Development/valkyrie`):
after a prior session fully solved the disc's compression/container layer,
one entire resource-tag family (`"FIS\0"`, 101 of 125 real decoded
records — the majority of the whole corpus) had already been found,
named, and given a working hypothesis ("field/scene data") based on
*indirect* evidence: other, differently-tagged sub-records chained
alongside it in the same container carried a real embedded mesh-name
string (`"Plane05"`) and animation-shaped tag names. That hypothesis was
never actually checked against the cheap direct test. Meanwhile, three
*other* investigative avenues were tried against the wrong search domain
entirely (TOC entries already confirmed to hold none of this format) — a
known texture-container magic scan, a palette-shaped byte scan, and a
documented platform-specific pixel-swizzle formula applied to an unrelated
resource family — all producing real, useful negative evidence, but none
of them finding the actual answer, because the actual answer wasn't in
that search domain at all. The eventual breakthrough was trivial once
tried: read the bytes after the `FIS` blob's 16-byte header as an 8-bit
raster at a couple of width guesses (128, 256) and render a contact sheet
across several real samples — instantly, unambiguously recognizable
(character portraits, a bitmap font, UI menu screens, a developer credit
screen reading "tri-Ace created"/"SQUARE ENIX").

**The generalizable move**: before spending more effort hunting for a
brand-new container/format in unexplored territory, first re-render
*every* already-decoded-but-only-heuristically-classified byte blob as an
image at a handful of width guesses — even ones that already have a
name and a plausible-sounding non-visual hypothesis attached. "Already
decoded, not yet actually looked at as pixels" is a distinct, nearly-free
check, separate from "not yet decoded at all" — and it's easy to skip
specifically *because* the bytes already have a working classification
(a magic tag, a bucket name, an indirect-evidence-based guess) that
doesn't visibly scream "nobody has tried rendering me yet." A named bucket
with a plausible story is not the same as a verified one.
