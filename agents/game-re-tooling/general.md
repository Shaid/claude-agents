# General tooling notes (all platforms)

> Moved verbatim from the always-loaded `game-re.md` during the 2026-10 restructure. `game-re.md` keeps the condensed rules; this file holds the full worked examples behind them. Read the section you need.

## Platform tooling-file table (full descriptions)

Load what the task needs; the skills contain the detailed workflows.

**Platform-specific tooling lives in `~/.claude/agents/game-re-tooling/`. `Read`
the file for your target before starting:**

| File | When |
|------|------|
| `game-re-tooling/amiga.md` | Any Amiga target — IRA disassembly and its `-preproc`/`-LABEL` traps, radare2's HUNK limitations, `amitools` for ADF/HDF, `openground` for HRM/RKRM lookups, amiberry operational gotchas, and the local scanned-manual archive that is often the only source of in-game *names* |
| `game-re-tooling/snes.md` | Any SNES/Super Famicom target — ROM header/copier-header/size-code conventions, radare2's native SNES support and its M/X flag-width blind spot, a half-width-katakana text-encoding shortcut for JRPGs |
| `game-re-tooling/switch.md` | Any Nintendo Switch target — `hactool` invocation and its silent-RomFS-dropout trap, why the **ExeFS must be extracted too** (it holds the resource-ID->filename registry that is often the only ID->name oracle), the `NSO0` + LZ4-block executable layout, and which container designs predict a path registry exists at all |
| `game-re-tooling/compression.md` | A payload looks compressed and the magic is unfamiliar — `ancient` identifies/decompresses dozens of retro codecs byte-exactly |
| `game-re-tooling/ghidra-loaders.md` | Ghidra/IDA can't parse your target's executable container, or a raw-binary import is losing segment layout, relocations or symbols — one loader per platform (PSX/PS2/PS3/PS4/PS5/PSP/Vita/Saturn/GC-Wii/DS/N64/Switch/Xbox), plus which platforms have no loader at all |
| `game-re-tooling/format-discovery.md` | An unidentified blob with no hypothesis yet — where to search for existing prior art on the exact game (QuickBMS/XeNTaX/binary-template corpora), the scriptable `reversebox` pixel-format + swizzle sweep, and the visualize-as-pixels / relative-search techniques worth reimplementing rather than reaching for a GUI. Also records which platforms the general "awesome game format" lists do **not** cover |
| `game-re-tooling/dos.md` | Any MS-DOS 16-bit real-mode target (`MZ` exe, `.ovr`/`.drv`) — the CS/DS segment-resolution trap for string/data xrefs, `.ovr` overlay-loader conventions, the launcher-`.bat`-as-load-order trick |
| `game-re-tooling/c64.md` | Any Commodore 64 / 1541 target — raw-GCR `.nib` decode traps (lenient-table phase search corrupts ~6% of sectors silently), custom-GCR-headers-over-stock-CBM-filesystem layering, the chain final-sector byte count, the multicolor bitmap+screen+colour-RAM three-part picture payload, radare2's 6502 address-display caveat |
| `game-re-tooling/cpc.md` | Any Amstrad CPC target — Extended DSK per-sector stored length (and the mislabeled-as-sector-count track-size table), fastloader disk-map recovery from boot load-call arguments, native mode-0/mode-1 bit-interleaved pixel layouts (never packed bit-pairs), Gate Array palette mapping, serpentine blitters, no hardware sprites |
| `game-re-tooling/atari-st.md` | Any Atari ST target — `.STX` (Pasti) floppy container structure and spec source, the desectorize-then-hand-off-to-mtools extraction technique, `mtools`' `MTOOLS_SKIP_CHECK` gotcha on GEMDOS media-descriptor bytes, disassembling a GEMDOS `.PRG` with Capstone (address<->file-offset resolution, the two-hop technique for finding OS/hardware calls hidden behind a shared trap trampoline) |
| `game-re-tooling/ps3.md` | Any PS3 target — classic-retail-PKG vs. Vita-"finalized"-PKG header confusion (why `pkg2zip` fails on genuine PS3 pkgs), the from-scratch AES-128-CTR decrypt algorithm + fixed key, NPDRM `.EDAT`/RAP-file decryption |
| `game-re-tooling/unreal-engine3-umodel.md` | Any UE1/UE2/UE3 target parsed via Gildor's umodel — why its `-export -gltf` CLI batch path can never embed animation data (a deliberate limitation, not a bug), the `.psa` (ActorX) headless workaround + its own distinct coordinate convention, and why AnimSet↔SkeletalMesh association needs bone-name-overlap ranking, not filename-convention guessing |
| `game-re-tooling/unreal-engine3-uelib.md` | Need actual readable UnrealScript source (not just confirmed-exists bytecode) from a UE1/UE2/UE3 `Class`/`Function`/`State` export — umodel can't decompile these at all; EliotVU/Unreal-Library (UELib) ships its own headless CLI (no Wine/Mono/GUI needed), but needs a forced `CookerPlatform=Console` and a cross-package native-function-table merge with a real eager-caching ordering trap |
| `game-re-tooling/ps2.md` | Any PS2 target — `xorriso`/`7z` ISO9660 parsing (often no UDF bridge), `SYSTEM.CNF`/EE-ELF/IOP-module conventions, the tri-Ace raw-LBA-archive pattern, and the PCSX2-savestate static VU1-tracing workflow (DMA/VIF chain decode + microcode disassembly — the authoritative reader when EE-side analysis stalls) |
| `game-re-tooling/psx.md` | Any PSX target — raw CD-XA MODE2/2352 sector layout (Form1 vs Form2 via the submode byte), radare2's native zero-config `PS-X EXE` auto-detection, and a reminder that Node's built-in `TextDecoder('shift_jis')` needs no extra package |
| `game-re-tooling/psp.md` | Any PSP target — the `fileOffset = vaddr + 0x60` ELF convention, a narrow ESIL-emulator false alarm that isn't a real Allegrex misdecode, resolving cross-module NID calls (which library/function a `jal` into another PRX's stub table really reaches) by parsing `.lib.ent`/`.lib.stub` directly from raw ELF bytes — including the tail-call-trampoline hop this often needs one more step past — and why a retail `~PSP`-tagged EBOOT is a hard blocker with no decrypt tooling on this account yet (check before promising eboot.bin disassembly as a fallback plan) |
| `game-re-tooling/seer-upstream.md` | You built or found code with zero game-specific logic that a second, unrelated project in the family also needs — which `@seer-project/*` package it belongs in, how to test it without vendoring copyrighted fixtures, and how to propagate a breaking rename/move safely across every sibling repo |
| `game-re-tooling/browser-viewer-testing.md` | Need to live-verify a fix/feature via Playwright against a seer project's dev server (live engine or `tools/viewer`) — no MCP playwright tool is usually registered and the project itself often has no `playwright` dependency; where to find a prior session's leftover install, and how to click a custom pan/zoom map/scene canvas reliably (screenshot-then-click, re-navigate before every click) |
| `game-re-tooling/mame-arcade.md` | Any MAME-format arcade ROM-set target (CPS1/2/3, System 16/18/24/32, Neo Geo, etc) — using the driver's own `ROM_START` source as a CRC32-matchable container oracle, `ROM_LOAD*` macro byte-copy semantics (`WORD_SWAP` vs `LOAD64_WORD` vs plain), and where per-game hardcoded encryption keys live for older sets (`historic-mame`) now that current MAME uses `.key` ROM files |

## Tool notes

- **radare2** (`Skill: radare2-amiga`, plus `mcp__radare2__*` via ToolSearch) —
  interactive disassembly, xrefs, hex dumps, byte-pattern search.
  Multi-architecture: the primary tool for DOS/x86 and other non-HUNK
  targets, and has native SNES/65816 support too (`-a snes`) — see
  `game-re-tooling/snes.md` for its flag-width blind spot. **It does not
  parse Amiga HUNK natively** — see `game-re-tooling/amiga.md`.
- **amiberry MCP** (`mcp__amiberry__*` via ToolSearch) — **hard gate: ask

  before you touch it, every time.** This is stronger than ordinary
  last-resort tool guidance — it's not "prefer not to," it's "must get
  explicit permission first." Exhaust static disassembly and structural
  verification (§4) before even considering it, then **stop and ask the
  user** (`AskUserQuestion`, or state the exact blocker in your report if
  you're backgrounded and can't block on a reply) rather than calling any
  `mcp__amiberry__*` tool unprompted — say what you need (e.g. "I need a
  register read while a Manta is rendered on screen") and let the user
  decide whether to grant you direct access or drive the emulator
  themselves and relay results. The user generally prefers to drive
  navigation/boot themselves rather than have an agent fight the IPC/boot
  process solo. **This applies to already-running and resumed sessions
  too** — if you haven't been explicitly granted amiberry access *this
  run*, ask before your first call even if a prior session used it freely;
  permission doesn't carry forward automatically.
  Operational gotchas once granted: `game-re-tooling/amiga.md` and
  `amiberry-live-capture-workflow.md`.
- **`Agent: explorer`** (haiku, read-only) — cheap high-level skimming of a
  large doc tree, unfamiliar codebase, or disassembly file before committing
  your own reasoning to it. Use it for Method §1's first pass over a large
  or unfamiliar file set, or before a `re-learn` scan-mode pass over a whole
  project's `docs/**`. Not for locating one specific known thing (that's a
  targeted grep, cheaper still) and not for judgment calls a decode's
  correctness hinges on — those need your own reasoning, not a haiku skim.
- **`Agent: reviewer`** (haiku, read-only) — cheap lint/type-check/syntax
  pass over a specific file or diff. Use it in Method §6's Promote step on
  new/changed extractor code instead of eyeballing lint output yourself.
  Not a substitute for the test suite (skips slow full runs) or for
  design/logic review — fast surface-level pass only.
- **Python** (numpy, PIL) for probes and committed extractors; **`npx tsx`**
  for pipeline code; **C + an emulator core** (musashi pattern) for hostile
  decompressors; `xxd`/`strings`/standard Unix tools for triage.
- **`vgmstream-cli`** — the reference decoder for Audiokinetic Wwise audio
  (`.wem`/`.bnk`, any studio/platform) and dozens of other game-audio
  container/codec families. Build from source
  (`github.com/vgmstream/vgmstream`, CMake) and vendor the CLI binary
  alongside other project tools (e.g. `tools/.bin/`) rather than hand-porting
  a codec's community tooling (`ww2ogg` for Wwise's stripped-RIFF "Custom
  Vorbis") — real risk of a byte-inexact decode for no benefit, see
  `standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`.
  It only emits WAV; pipe through `ffmpeg` for the project's real output
  codec. Its `-I`/info-style flags are not automatically side-effect-free —
  see `info-only-flag-not-side-effect-free.md` before looping any query flag
  over original game data. **When a container shares a known family's magic
  but doesn't decode with that family's already-solved reader** (right
  header, wrong internals — a hand-reimplemented decoder returns 0
  streams/garbage against real bytes that otherwise look plausible), read
  vgmstream's own `src/meta/<family>.c` source directly rather than
  treating the CLI as an opaque black box or assuming no more prior art
  exists — one shared outer magic can wrap more than one structurally
  distinct sub-format (confirmed on Three Hopes' `ktsr.ts`: a `"KTSR"`-
  magic "ktsl2stbin" reader, already verified on one sub-format, was blind
  to a second, `ASRS`-wrapped "as"/audio-set bank sub-format the same
  engine also ships — `vgmstream`'s `ktsr.c` had a dedicated entry point
  for it that the project's other reference sources, an 010-template repo
  and a fan Python toolset, didn't cover at all).
- **Bash gotcha: double-quote-adjacent braces silently stall you.** The CLI
  flags any command with a `"` immediately next to `{`/`}` (e.g. `f"{x}"`
  inside `python3 -c "..."`) as "brace with quote (expansion obfuscation)"
  and forces a manual permission prompt — no allowlist rule suppresses it
  (compiled into the binary), and it's fatal when backgrounded. Never write
  double-quoted f-strings/dict-literals/format-specs in a Bash command. Use
  `python3 << 'PYEOF' ... PYEOF` (single-quoted delimiter) with single-quoted
  f-strings (`f'{x:04x}'`) for one-liners, or write the probe to a scratch
  file and run the brace-free `python3 /tmp/probe.py` for anything longer.
- **Bash gotcha: `grep` silently finds nothing in Latin-1/ISO-8859 source
  files.** A `.cs`/`.c`/legacy source dump with non-UTF-8 bytes (accented
  characters in comments, etc.) gets classified as "binary" by `file`, and
  plain `grep -n pattern file` then matches nothing at all — no error, no
  warning, just zero hits, even for patterns you can see in a `Read` of the
  same file. Always pass `-a` (treat as text) when grepping a fan-tool
  source dump, decompiled output, or any file `file` reports as anything
  other than ASCII/UTF-8 text.
- **`Skill: re-codebreaker` / `Skill: re-oracle`** — model escalation, see the
  ladder above.
- **`Skill: re-learn`** — the learning loop: distills durable lessons into
  the knowledge base via an inbox + locked curation pass. See `game-re.md`'s Learning loop.
