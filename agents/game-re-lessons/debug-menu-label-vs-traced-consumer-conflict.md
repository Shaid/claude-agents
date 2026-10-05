# A factory debug-menu label is real data, but not automatically more authoritative than a traced consumer

**When it bites:** a factory/test-menu "memory viewer" or "object list"
label table gives a RAM region/structure a plain-English name (e.g.
"BOSS WORK"), and that name disagrees with a semantic identification
you already established for the exact same region by tracing a real
consumer (a name-display routine, a spawn mechanism, a stat-init entry
point). Before overwriting the traced identification with the debug
menu's label — or vice versa — stop and check whether you actually have
grounds to prefer one over the other.

Both a debug-menu label and a traced consumer are real, verifiable
evidence classes, but they answer different questions: the label is
whatever a factory engineer typed into a memory-viewer tool (which may
be copy-pasted from an internal template shared across several titles,
or may use in-house jargon that doesn't map cleanly onto an outsider's
guess at "what the English word means"); the traced consumer shows what
the shipped game code actually *does* with that region. Neither is
inherently more authoritative, and a mismatch between the two is a real,
citable finding — not an error to silently resolve in either direction.

Confirmed on D&D: Shadows over Mystara (CPS2, `kolbold`): a factory
"GAME WORK" debug menu's own label table named the two character object
pools "BOSS WORK" (22 slots) and "ESHL WORK" (3 slots) — the *opposite*
of an already strong, independently-traced identification from a
different angle (the 3-slot pool's spawn code installs a pointer into a
boss health-bar-and-name UI object that displays a real, confirmed
21-entry monster-name table; the 22-slot pool has no such name-display
mechanism and includes at least 2 confirmed "one-hit breakable scenery"
types). Both facts are independently well-evidenced; the debug menu's
"BOSS" label could be an inherited template name that no longer matches
this specific game's memory layout, or "boss" could mean something
broader in the developer's internal usage than "the on-screen
end-of-stage antagonist" — there's no way to tell from the label alone.

**Fix:** report both facts side by side, explicitly flagged as an open
tension, rather than letting the more recently-found or more
literally-named source silently override the other. Keep whichever
identification is tied to a *directly traced consumer* as primary in any
downstream extractor/doc that depends on the semantic role (not just the
address), and record the debug-menu label as independently-confirmed
real content in its own right.
