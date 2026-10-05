# The radare2 MCP `open_file` tool's `baddr` can silently fail to map a raw/`format: null` file — verify with a landmark before trusting any address

**When it bites:** you call `mcp__radare2__open_file` with `arch` and
`baddr` set on a raw/headerless blob (no ELF/PE/Hunk magic — `show_info`
reports `format: null`), expecting the file's byte 0 to appear at `baddr`
the way `r2 -m <addr>` on the CLI would place it. If the map didn't
actually take, every subsequent `disassemble`/`hexdump`/`xrefs_to` call
you make using the game's real runtime addresses (the ones cited in your
own project docs, `mem $X = file_offset + baddr`) is silently querying the
**wrong location** — no error, just plausible-looking wrong bytes/garbage
disassembly, or all-zero reads at the address you expected content.

Confirmed on Deuteros (Amiga, `methanoid`): `open_file(file_path=
"track80_payload.bin", arch="m68k", baddr="0x13000")` reported success,
but `hexdump` at `0x13000` read all zeros while the file's own
already-doc-confirmed leading `jmp $40434.l` header showed up at address
`0x0` instead — i.e. **the requested `baddr` had no effect**; every r2
address in that session was a plain raw file offset, not the runtime
address. This cost real time two ways: (1) an unvalidated linear capstone
disassembly (decode from offset 0, advance by each decoded instruction's
size) produced silently-wrong "hits" that looked like real operand
matches; (2) even after switching to an alignment-safe byte-pattern scan
(search for a fixed opcode word immediately followed by its 4-byte
absolute operand — safe against linear desync), the first attempt to
cross-check a hit against r2 queried at `file_offset + baddr` instead of
plain `file_offset`, and appeared to "refute" a real, correct hit before
the addressing bug was found.

Also confirmed in the same session: `xrefs_to` returned **zero output for
every address tried, code and data alike**, for the whole session, even
after running `analyze` (level 1, 1084 functions found) — it was not a
reliable tool for this raw target at all, consistent with (and worth
reading alongside) `mcp-radare2-search-sandbox-error.md`'s report that
`search` is also unreliable on freshly-opened raw binaries in this MCP
session. Direct `disassemble`/`hexdump` calls plus independent
byte-pattern verification were the only techniques that worked.

**Fix:** immediately after `open_file` with a `baddr` on any raw/
headerless file, verify the map actually applied with one cheap landmark
check before trusting anything else — `hexdump`/`disassemble` at address
`0x0` *and* at the requested `baddr`, and confirm the file's real known
content (a documented header, a byte-exact string, anything already
confirmed by another method) shows up where you expect. If it shows up at
`0x0` instead of `baddr`, the map didn't take: every address in that
session is a **plain file offset**, and every runtime/doc-cited address
must be manually translated (subtract the load base) before use —
including addresses that appear as **operands inside disassembled
instructions**, since those are real baked-in runtime addresses from the
compiled code, not r2 addresses, and need the same subtraction before you
hexdump/disassemble whatever they point to. Don't assume a fix that works
on the CLI (`-m <addr>`, see `r2-arch-flag-before-dashdash-file-separator.md`)
transfers to the MCP wrapper's `baddr` parameter without the same
landmark check — they are different code paths and this session showed
the MCP one can fail silently where the CLI one at least tends to fail
loudly (all-`0xFF`/empty reads).
