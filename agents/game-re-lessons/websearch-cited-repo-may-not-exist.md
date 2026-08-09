# A WebSearch-cited repo URL may not exist even when a related page is real

**When it bites:** `WebSearch` surfaces a GitHub repo as prior art for the
exact game/format you're working on — especially one with a suspiciously
perfect-sounding description ("fully reverse-engineered," "N functions
mapped," "bit-exact").

Search grounding can hallucinate a specific repo owner/name/URL even when a
genuinely real page about the same project exists at a *different* URL.
Confirmed on Midwinter (Amiga): `WebSearch` returned
`github.com/DrEvil-TitaniumHelix/midwinter-decode` with a detailed-sounding
description — `curl`/`WebFetch`/the GitHub API all return 404, the repo does
not exist — while a real writeup of the same underlying project was live at
`midwinter-remaster.titanium-helix.com/decode`, a completely different
domain. The fabricated repo URL was plausible enough (right org-name style,
right topic) that treating it as real without checking would have wasted a
`git clone` / tarball-download cycle (which it did, briefly) before the 404
surfaced.

**Fix:** before spending any real effort on a WebSearch-cited repo (cloning,
downloading a release, reading its docs as ground truth), confirm it exists
with a cheap check — `curl -s https://api.github.com/repos/<owner>/<repo>`
(no auth needed for public repos) or a `WebFetch` on the repo's own page —
*before* trying to clone it. A 404 doesn't mean the underlying claim is
false, only that the specific URL is wrong; re-search or follow other links
in the same result set (the real page is often one result away, as it was
here).
