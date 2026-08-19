# A curated `www/` site page can restate a raw doc's *old* verdict after the raw doc was corrected

**When it bites:** you're editing a `www/` site page (or any other curated
summary surface) that cites a specific item as open/unresolved/hypothesis,
and you're about to add new content near that citation without first
checking whether the raw `docs/<game>/` notes it summarizes still say the
same thing.

The seer framework's site convention (`WRITING-GUIDE.md` rule 8, the
`seer-website` skill) states the raw notes are the source of truth and "when
a page contradicts the notes, fix the page" — but that's a rule for the
*next* editor to follow, not a guarantee any previous page-authoring pass
actually re-checked it. A raw doc can get corrected in one session (a
`re-codebreaker` escalation resolves an "open" item, a later disassembly
pass finds the real table) with no corresponding pass ever touching the
`www/` pages that had already summarized the old, wrong verdict. The two
surfaces drift silently — the site keeps building and reads perfectly
plausibly, because nothing about a confidently-worded "not located" or
"still open" paragraph signals that it's stale.

Confirmed on nicodemus (Phantasie III): `docs/phantasie/data-tables.md` had
resolved both the P3 race→sprite-bank-cell table (§4.2, "LOCATED AND
CONFIRMED," including a correction block dated two days before this pass)
and `inititem.dat`'s field semantics (§6.4, "the array orientation was
transposed") in a prior session. Five files under `www/src/content/docs/`
(`phantasieiii/data-tables.md`, `sprites.mdx`, `graphics.md`, `status.md`,
`index.mdx`) plus `docs/phantasie/implementation-plan.md`'s own status
table still described both as open/unverified-hypothesis, unchanged since
before the raw-doc correction landed. This surfaced only because a new
`DataTable.astro` page was about to render the *resolved* race→cell table
live, right next to prose that called the same table "not located" — an
internal contradiction on one page is what caught it, not a deliberate
audit.

The fix that generalizes: whenever you are about to publish new
site content that touches a format/table/mechanism a site page already
describes, re-read that page's existing claim against the current raw doc
section it should trace back to (not from memory of what the raw doc said
when you last read it, and not by trusting the site page's own confident
tone) before writing new prose next to it. A live rendered table showing
data a nearby paragraph calls "not located" is the sharpest version of this
check — if you're building exactly that kind of component, look for it
deliberately. This is a targeted spot-check anchored on what you're already
editing, not a full-site staleness audit (that's the `seer-website` skill's
audit mode, a separate, heavier pass) — but it's cheap and catches the
specific case where new work would otherwise ship *next to* a contradiction
it could have fixed for free.
