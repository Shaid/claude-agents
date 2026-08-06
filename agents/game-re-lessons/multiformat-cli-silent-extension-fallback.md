# A multi-format CLI decoder's silent success on a renamed file doesn't mean it took the format-specific code path

**When it bites:** shelling out to a community multi-format decoder/probe
tool (vgmstream, ffmpeg, a generic container-sniffing utility) against a
file whose real on-disk extension doesn't match the target format's usual
extension (a renamed/relabeled asset dump, e.g. `.XXX`/`.bin`/`.dat`
instead of `.wav`/`.ogg`/`.scd`) — especially when the tool *appears* to
work (exits 0, produces plausible-looking output) for most files in a
batch.

Many multi-format CLI tools dispatch to a format-specific parser based on
the file's extension, and fall back to a generic content-sniffing/auto-
probe path when the extension doesn't match anything they recognize —
**silently, with no warning that the specialized parser was skipped.**
Confirmed on Drakengard 3 (PS3, `flower` project): `vgmstream-cli` run
against a Square Enix SCD container with its real on-disk `.XXX` extension
does not fail — it falls back to a generic FFmpeg-format auto-probe
(visible only in its own `-I` JSON output as
`"metadataSource":"FFmpeg format (...)"` rather than the real parser's
`"metadataSource":"Square Enix SCD header"`) that happens to find valid
MP3 sync frames near the start of the raw container bytes for most files,
purely because the container's own header bytes didn't happen to collide
with an MP3 frame sync pattern. This "worked" for 1780/1793 files in an
initial batch scan (looked like a clean, if slightly imperfect, result) —
but it silently skipped the format's real subsong-table/loop-point/codec-
dispatch logic entirely, and **outright failed** on the corpus's 3 files
using a different internal codec (raw PCM, not MP3) that the generic MP3
auto-probe couldn't accidentally find. Renaming/symlinking the same files
to the extension the tool's own source-level format check requires (here,
literally a `check_extensions(sf, "scd")` call inside the format-specific
parser, confirmed by reading the tool's source) fixed both problems at
once: the real parser ran for every file, and all 3 previously-"failing"
PCM files decoded correctly.

**The fix, generalized**: before trusting a multi-format CLI tool's output
against a file with a non-standard extension, either (a) rename/symlink
the input to the extension the target format's own parser expects, or (b)
read the tool's source (or its verbose/JSON diagnostic output, if it has
one — many do report which internal parser/metadata-source actually
matched) to confirm which code path actually ran. A clean exit code and
plausible-looking numbers are not sufficient evidence the specialized,
format-aware parser executed — they're equally consistent with a generic
fallback that happened to produce a coincidentally-reasonable result for
the *majority* of a corpus while being silently wrong for the rest. This
is a distinct trap from "the tool doesn't support this format at all"
(which usually errors loudly) — it's specifically about tools that support
the format but gate entry to that support on a naming convention the
renamed asset dump doesn't follow.
