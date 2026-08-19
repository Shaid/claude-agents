# A background agent that spawns its own sub-agent and waits for it stalls repeatedly

**When it bites:** you are running as a background/forked agent and are
about to spawn a generic sub-agent (`Agent` tool / a fork) for part of your
task and *wait* for its result — or you just wrote "waiting for its
notification" as your final message.

Confirmed three times in one day (middilgard, 2026-08): a code-review agent
and a game-re completion agent (twice) each spawned children and stopped to
"wait for the notification". The wake-up never arrives the way it does for
the top-level session: the parent *stops*, the child's completion either
fires a notification to the top-level coordinator instead (who has to relay
it back down by hand), or the child's report can't even route to the parent
at all (one child's `SendMessage` to its parent's name failed to resolve and
it delivered its entire result to `main` as a fallback). Each stall cost a
human-noticeable delay and two coordinator interventions; one produced
duplicated work when the parent was told to redo what its lost child had
already finished.

What to do instead, inside a background agent:

- Do the work **synchronously yourself**, or through the escalation
  *skills* (`re-codebreaker`/`re-oracle`) — their fork-and-return contract
  is the one path that reliably delivers results back into your run.
- If you genuinely need parallel reads, use synchronous tools in one
  message (parallel tool calls), not spawned agents.
- Never end your turn "waiting" on a child: if you must spawn one, treat
  its result as potentially lost — before stopping, either collect it via
  TaskOutput in the same run or write your report assuming you may not be
  resumed.

Coordinator side (the session that launched you): when briefing agents for
completion campaigns, say explicitly "do NOT spawn generic sub-agents and
wait on them" — the two runs briefed that way finished cleanly in one pass;
the one briefed without it stalled twice.
