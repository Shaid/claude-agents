# A CLI tool's "info"/"metadata"-sounding flag can still write output — verify it's actually side-effect-free before trusting it near `data/`

**When it bites:** running any external tool's query/info/metadata flag
(disassembler `-info`, media-decoder `-I`/`--info`, etc.) directly against a
file inside `data/<game>/<platform>/` (or an already-decrypted romfs dump
under `data/extracted/`) — especially in a loop over many files, and
especially before trusting that directory's file inventory/count for
anything afterward.

## Three confirmed instances, two different tools

**IRA (disassembler), sub-agent-driven:** IRA's `-config`/`.cnf` workflow,
and some sub-agents driving it, default to writing their `.cnf` config file
(and sometimes the `.asm` output too) into whatever directory they were
invoked from or found the target binary in — which, for a seer project, is
often `data/<game>/<platform>/` itself, the one zone the whole framework
contract says is never modified by code. This happened silently in a
Wizardry 6 Amiga session: an `amiga-disasm` sub-agent disassembling `Bane`
left `Bane.cnf` sitting next to the original game files, changing a
verified "117 files" inventory to 118 with no error or warning — only
caught because a later step re-counted files by extension as a sanity
check, not because anything failed loudly.

**IRA, no sub-agent involved:** running IRA yourself with an `-info`-only
invocation and no explicit `TARGET` argument (e.g. `ira -info
data/<game>/<platform>/Foo`, just checking hunk sizes before the real
disassembly pass) still writes `Foo.asm` next to `SOURCE` by default —
confirmed on Embryo (Amiga): a first `-info` call with only `SOURCE` given
left `Embryo.asm` sitting in `data/explore/EmbryoHr/data/` even though the
*real* disassembly pass moments later correctly wrote to `docs/.../Embryo.asm`
because that one specified `TARGET` explicitly.

**`vgmstream-cli` (audio decoder), an unrelated tool and domain entirely:**
`-I` (print file info as JSON) looks exactly like a query-only flag — the
usage text and every intuition about a flag named "info" say so — but it is
**not** metadata-only. Unlike `-m` (`print metadata only, don't decode`),
`-I` does not set the tool's internal "metadata only" flag; per its own
source (`cli/vgmstream_cli.c`'s `process_file()`), `-I` only selects
JSON-formatted printing, and execution still falls through to a full
decode-and-write using vgmstream's *default* output naming
(`<infile>.wav`, or `<infile>#<subsong>.wav` for multi-stream sources)
whenever no `-o` is given. A metadata-sweep helper for Astral Chain (Switch)
that queried every `.wem`/`.bnk` subsong's sample rate/channel count/short-ID
via `-I` alone silently wrote **11,818** stray `.wav` files directly into
the read-only `data/extracted/.../p0-romfs/sound/` tree — one next to every
loose `.wem`, one per queried `.bnk` subsong — a real violation of the
"never modify `data/`" zone rule. It was caught only by an unrelated
investigation (diffing an update-patched romfs against the base one) that
noticed an unexplained `.wav` file-extension population next to the
expected `.wem`/`.bnk`/`.wai` files. Fix: always pass `-m` together with
`-I` (`-I -m`) for a query that is genuinely side-effect-free; confirmed
this combination still returns full JSON metadata (including per-subsong
`streamInfo.name`/`.total`) while writing nothing.

## The general lesson

A flag's name and even its one-line usage description are not proof it has
no side effect — verify empirically, once, before trusting it in a loop:
run it once against a throwaway copy of one file (or, if it must run
against the real corpus, on the very first invocation) and diff `find
<target dir> -newer <marker>` before/after. This is the same "trust but
verify" the delegate-to-a-reference-decoder pattern already recommends for
*decode correctness* (see `standard-codec-delegate-to-trusted-decoder-not-
hand-reimplementation.md`) — it applies equally to a tool's read-only-looking
flags, not just its actual decode output. Two habits prevent/catch this in
general: (1) after any external tool delegation (disassembler, decoder,
archiver) touches `data/`, re-run a file count/extension histogram on that
directory and compare against the session's earlier known-good inventory —
a diff of exactly the tool's own output-file naming convention is the
signature; (2) prefer routing any tool invocation's output explicitly (an
`-o`/`--output`/`TARGET` argument into `docs/` or a scratch dir) over relying
on a tool's own default-output-location behavior, even for what looks like
a read-only query call.
