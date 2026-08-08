# A container/compression format "confirmed" via one working consumer tool may only be half-understood — a second sub-format can hide until a different consumer needs raw bytes directly

**When it bites:** a container/compression wrapper format has already been
declared "confirmed, byte-exact" based on a real, working consumer tool
(umodel, a community extractor, an emulator's own loader) successfully
reading files that use it — and a **second** tool/pipeline stage now needs
to read the *same kind* of file, but by parsing raw bytes directly rather
than shelling out to the first tool. The second tool fails (crashes,
hangs, or misparses) on files the first tool has always handled fine.

Confirmed on Drakengard 3 (PS3, `flower`): the project's own
`decompressXxxChunks` was documented as "the format wrapping every
`.XXX`-suffixed file," verified byte-exact — but that verification sample
only ever included 4 core/script packages (`CORE.XXX`/`ENGINE.XXX`/
`GAMEFRAMEWORK.XXX`/`SQEX03GAME.XXX`), because those were the only files a
prior pass needed to feed to UELib directly. umodel had been reading
*every* `.XXX` file in the corpus correctly the whole time — including
Level/Map packages, which turned out to use a **second, structurally
different** on-disk sub-format (a plain header + an embedded
`CompressedChunks` table addressing separately-compressed regions, vs. the
whole-file-wrapped shape the "confirmed" format actually described). This
went completely unnoticed for the entire prior duration of the project,
because umodel's own C++ decompressor already branches on both shapes
internally and never surfaced the distinction to anything downstream.

**The generalizable trap**: "a consumer tool reads this file type
correctly" is evidence the *tool* handles the format(s) present, not proof
you (or a from-scratch parser) understand the *one* format the file type
actually uses — a mature tool routinely supports several on-disk variants
transparently, silently, and without logging which one it picked. A
"byte-exact confirmed" claim inherits the sample bias of whatever files it
was checked against; if that sample was narrow (all one content *kind* —
here, script/core packages vs. ordinary level/asset packages), a real
second sub-format restricted to the untested kind can sit completely
undetected until something forces raw-byte-level parsing of it directly.

**What to do differently**: when a container format was only ever
*verified* against a narrow content-kind sample (even if that sample was
itself rigorously checked), and a new task needs to parse a *different*
content kind's files the same way, re-derive/re-check the format against
a representative file of the new kind before assuming the old derivation
covers it — don't extrapolate "confirmed on N files" to "confirmed for the
whole corpus" without checking the new kind specifically. When the
existing tool's own source is available (as with umodel/UEViewer's C++),
finding the *second* sub-format's exact byte layout by reading that tool's
own reference deserialization code (not guessing/fuzzing) is fast and
reliable — the tool already solved this correctly; a second, from-scratch
parser just needs to catch up to it, not re-derive it independently. When
integrating the fix, prefer **auto-detection between the known sub-formats**
(try the already-working one first, fall back on failure) over adding a
manual format-selection flag — this generalizes to any file automatically,
including the ones already proven to use the original format, with a
built-in regression check (the original format's own files must still
round-trip identically through the auto-detecting entry point).