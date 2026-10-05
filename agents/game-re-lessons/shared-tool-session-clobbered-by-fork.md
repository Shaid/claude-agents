# A forked escalation — or an unrelated concurrent session — can silently repoint your own shared MCP tool session

**When it bites:** you've verified something with a stateful MCP tool
(radare2's open file, an emulator's loaded ROM, any tool with server-side
"current context" rather than a fresh call each time), then either launch a
`re-codebreaker`/`re-oracle` fork or any other subagent that uses the same
MCP server, *or* an entirely separate, independently-running sibling
session happens to share the same MCP server against the same project —
and you're about to trust a *new* call to that tool without re-establishing
its state first. The two triggers (your own fork; an unrelated concurrent
session) produce the identical symptom and need the identical fix — you
usually can't tell which one clobbered you, and it doesn't matter.

Strike (Mega Drive): the orchestrator opened Urban Strike's ROM in the
`mcp__radare2__*` MCP session and disassembled a known-good address,
confirming sane output. It then launched a `re-codebreaker` fork over the
same MCP radare2 server to trace a dispatch table. When the fork returned
with claimed disassembly addresses, the orchestrator re-disassembled the
*same already-verified* address as a canary before trusting the new ones —
and got garbage/`invalid` instructions, on an address that had disassembled
correctly minutes earlier. The fork's own radare2 usage had silently left
the shared server pointed at a different file (or a different arch/seek
state); nothing crashed or errored, it just started answering from the
wrong context. `close_file` + `open_file` with the original arch/baddr
restored correct output immediately, and the escalation's claimed addresses
then disassembled exactly as reported.

The fix pattern, and why it's cheap: before trusting any post-escalation
tool call against a stateful MCP session, re-check one already-known-good
reference point first (or unconditionally re-open/reset the session). If
the canary comes back wrong, the *session* is the problem, not the
escalation's claims — don't waste time doubting the escalation's findings
before ruling this out. This is a distinct failure mode from
`verify-escalation-artifacts-not-just-claims.md` (which is about the
escalation's own returned artifacts going stale) — here the escalation's
claims can be perfectly correct, but *your own verification tooling* is
reading from the wrong place until reset.

**A cheap, always-available discriminator that needs no canary re-check:
does the returned address even fall inside the file you *meant* to have
open?** Confirmed a third time, same project (Valkyrie Profile, PSX), no
escalation in flight at all — just switching `open_file` from one raw
overlay blob to another within one session (`show_info` correctly reported
the new file afterward). `xrefs_to` on addresses belonging to the
*previous* file (well below the new file's own load-base-to-load-base+size
window) still returned confident-looking hits, complete with plausible
`fcn.*` labels and instruction text matching facts already documented
elsewhere about that *previous* file — easy to mistake for genuine
analysis of the new file if you don't check. Every `xrefs_to`/
`disassemble`/`decompile_function` result on a raw/headerless binary should
be sanity-checked against the currently-open file's real mapped address
range (`baseAddr` to `baseAddr + fileSize`, from your own `open_file` call
or `show_info`) before citing it — a result whose address (or whose *from*
address, for an xref) falls outside that window is stale, not evidence
about the file you think you're analyzing. Because this doesn't require
knowing in advance which address is "already good," it's a strictly
cheaper check than the canary re-disassembly above, and catches the same
underlying failure (fork collision, sibling-session collision, or —as
here— the MCP wrapper's own analysis database not being cleared across an
`open_file` switch) with no extra round trip.

**No fork involved — a wholly independent sibling session hit the same
radare2 MCP server, three times in one session.** Valkyrie Profile (PSX,
`valkyrie` project): a session doing pure static disassembly (no
`re-codebreaker`/`re-oracle` calls in flight) had its `mcp__radare2__*`
session's open file silently swapped to a *different* game overlay by an
unrelated concurrent sibling session working the same repo — caught once
via `show_info` reporting an unexpected filename outright, and once more
subtly via a `hexdump` result that read as plausible, self-consistent MIPS
disassembly but flatly disagreed, byte-for-byte, with a direct read of the
same file/address done independently. Two concrete, cheap habits caught
every occurrence before it produced a wrong conclusion: (1) call
`show_info` (or equivalent) and check the reported filename any time
there's been a gap since the last confirmed-good call — another tool call,
a wait, a round-trip to a coordinator — before trusting the next result;
(2) when a result looks even slightly suspicious, cross-check it with a
*second, independent* read of the raw file that bypasses the MCP session
entirely — for a disassembler, decode a handful of raw instruction words
directly (e.g. Python `struct.unpack_from('<I', data, vaddr - baddr)` on
the actual file) and compare by hand; a genuine MIPS opcode/register
decode either matches the tool's claim exactly or it doesn't, with no room
for interpretation. This is *more* reliable than re-querying the same MCP
tool again, precisely because it doesn't depend on that tool's session
state at all.
