# A forked escalation can silently repoint your own shared MCP tool session

**When it bites:** you've verified something with a stateful MCP tool
(radare2's open file, an emulator's loaded ROM, any tool with server-side
"current context" rather than a fresh call each time), then launch a
`re-codebreaker`/`re-oracle` fork or any other subagent that uses the same
MCP server, and are about to trust a *new* call to that same tool without
re-establishing its state first.

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
