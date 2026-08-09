# The identical confirmed magic can denote two structurally-unrelated formats, disambiguated only by referencing context

**When it bites:** a container format you've already solved for one magic
turns up again behind a *different* referencing tag/pointer/directory
entry type in the same game, and you're about to assume "I already know
this format" instead of actually parsing its bytes.

Valkyrie Profile 2 (PS2) has an already-solved `"FAS\0"`-tagged container:
a flat list of named placement objects (16-byte name + a small transform
sub-record), confirmed as title-screen menu-button placements when reached
via one resource-directory tag (`PAM\0`, "MAP" reversed, adjacent to
`RMAC` menu-string records). A later pass found the *identical* 4-byte
`"FAS\0"` magic reached via a completely different resource-directory tag
(`MINA`, "ANIM" reversed) — and it turned out to be a wholly unrelated
container: a flat list of named *bone animation tracks*, each holding a
per-frame quaternion keyframe array. Same 4 leading bytes, same broad
shape ("a list of named things with sub-records"), completely different
content and internal record structure. The only signal distinguishing
them is the *outer* tag that led to each record — the inner magic alone
is not a reliable format identifier here.

This project had already independently established that literal
(non-reversed) internal tags get reused across contexts (`IDOM`, `FAS`,
`RMAC` all recur in more than one role elsewhere in the same corpus) —
this is the sharpest instance of that pattern: not a *near-miss* reuse
(a shared struct with one field repurposed, see
`sibling-magic-may-be-same-struct-zeroed-field.md` for that *different*
situation, a one-character-different sibling magic) but the *exact same*
magic, fully unrelated content, disambiguated purely by the outer
container's own tag.

General rule: when a new occurrence of an already-solved magic turns up
behind a *different* referencing path (a different directory tag, a
different pointer table, a different parent container instance) than the
one it was originally solved against, don't skip straight to reusing the
old decoder — spot-check a few bytes against the old struct's own
confirmed field layout first. A mismatch there is real signal that you're
looking at format reuse of the tag, not the format.
