# The MCP radare2 `search` tool can refuse every query with "Sandbox restricts search range"

**When it bites:** you open a freshly-loaded binary in the `mcp__radare2__*`
MCP session and reach for the `search` tool (string, hex, or value type) to
find a hardware-register constant, a magic, or a literal — and it returns
`[ERROR] Sandbox restricts search range` for every query you try, including
trivially well-formed ones (a plain ASCII string search, a 4-byte value
search on an address you already know is in-range from `show_info`).

Confirmed on Valkyrie Profile (PSX): opening the raw `SLUS_011.56` PS-X EXE
(radare2 auto-detects `format: psxexe` correctly, `show_info` reports sane
`size`/`arch`/`bits`) and calling `search` with `type: "string"` for
`"MDEC"`, or `type: "value"` for a 4-byte hex constant, both failed with the
identical sandbox error — not a malformed-query error, and not specific to
one query type. This isn't a "your syntax is wrong" signal; the MCP
wrapper's search command is blocked outright for reasons that don't surface
any further diagnostic.

**The fix isn't to debug the query — it's to stop trusting `search` as
available at all and fall back to a direct read.** For finding
opcode/instruction-shaped patterns (e.g. a MIPS `lui reg,imm` immediate, an
absolute address embedded across an instruction pair), read the raw file
bytes yourself (Python `struct.unpack_from`) and decode the fixed-width
instruction encoding directly — this is strictly more reliable anyway since
it doesn't depend on any tool's internal addressing/base-address state (see
`shared-tool-session-clobbered-by-fork.md`). For a plain string literal,
`mcp__radare2__list_strings`/`list_all_strings` still works even when
`search` doesn't (confirmed on the same session) — try that before assuming
the whole MCP server is unusable. Reserve `xrefs_to` for a specific
already-known address once you've found your target some other way; it
worked normally throughout the same session that had `search` blocked.
