# Invoking `r2`/`radare2`/`rasm2` directly via the Bash tool silently reads all-0xFF instead of the real file

**When it bites:** you reach for the plain `r2`/`radare2`/`rasm2` CLI via
the Bash tool (not the `mcp__radare2__*` MCP tools) to do a quick
disassembly or hexdump — e.g. of a small extracted blob in the session
scratchpad, or even an ordinary in-repo file you've read successfully
with other tools — and the output looks structurally valid (correct
byte count, correctly-formatted hex/disassembly columns) but is
uniformly `ff ff ff ff ...` / `invalid` for every offset, including for
files you independently confirmed have real content (`xxd`/`Read` on the
same path shows real bytes).

Confirmed on Reunion (Amiga AGA, `methanoid`): `r2 -q -c 'px 32' --
build/cache/reunion/amigaaga/game.exe` (a normal, already-decompressed,
in-repo Hunk executable, definitely not sandboxed-away) returned uniform
`ffff` bytes at every offset — not an error, not a "file not found," just
silently wrong content that *looks* like a legitimate (if boring) hexdump.
The same file opened via `mcp__radare2__open_file` +
`mcp__radare2__hexdump` immediately showed the correct bytes. This isn't
a path-based sandbox exclusion (scratchpad vs. repo made no difference —
both failed identically via Bash) — it's specific to shelling out to the
`r2`-family binaries under the Bash tool's sandboxing, which appears to
intercept/deny the raw file read the binary performs and hand it a
filled buffer instead of a clean error.

**The fix:** never shell out to `r2`/`radare2`/`rasm2` via the Bash tool
for anything that reads real file content — always use the
`mcp__radare2__*` MCP tools (`open_file`, `hexdump`, `disassemble`,
`search`, etc., loaded via `ToolSearch` if not already in context). If a
tool call the MCP server doesn't expose is genuinely needed, don't fall
back to the Bash CLI silently — the all-0xFF result is indistinguishable
from a legitimately blank/erased region at a glance, so a raw Bash `r2`
result should never be trusted as ground truth about a file's contents
without cross-checking against an independent read (`xxd`, `Read`, or
the MCP tools) first.

Distinct from `mcp-radare2-search-sandbox-error.md` (a specific *MCP*
tool call, `search`, failing loudly with an explicit sandbox error
message) and `shared-tool-session-clobbered-by-fork.md` (a stateful MCP
session silently repointed to the wrong file by a concurrent user) — this
one is the plain CLI, invoked directly, failing *silently* with
plausible-looking wrong output, on a file that is not shared/stateful at
all.
