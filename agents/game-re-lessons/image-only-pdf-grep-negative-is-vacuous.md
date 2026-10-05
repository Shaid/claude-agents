# A "grep/pdftotext the manual, found nothing" negative is vacuous if the PDF has no text layer at all

**When it bites:** about to trust — yours or a prior round's — "checked the
manual/rulebook/strings and found no mention of X" claim against a scanned
document, without first confirming the PDF actually has an extractable text
layer; or a long-deferred item's own history contains an unexplained "a
quick check ... found none" line with no cited command or page range.

This is a distinct, earlier-stage failure from
`scanned-manual-paraphrase-needs-reverify-and-diff.md` (which is about
trusting an already-*read* paraphrase without re-diffing the page images).
This one is about a negative that was never capable of finding anything in
the first place: many first-party scanned manuals are pure page-image scans
with **no text layer** — `pdfinfo` on one such file reported `Producer:
Adobe Acrobat 6.0 Image Conversion Plug-in`, and `pdftotext -layout` on it
returned empty output for all 19 pages. Any `grep`/`pdftotext`/OCR-less
text-search check run against a file like this returns zero hits
regardless of what the manual actually says — a structurally guaranteed
false negative, indistinguishable in its own output from "really isn't
there."

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a multi-round item
(`vp1psx-object-kind-7-8-unattributed`) had been carrying a one-line "a
quick check for ... a scanned-manual mention found none" verdict for
several rounds, treated as confirming the mechanism genuinely had no
official name and was `deferred:live-capture` for that reason alone. Running
`pdfinfo` on the manual showed it was an image-only scan; reading it with
the `Read` tool's `pages` parameter (which renders PDF pages as images,
not text) surfaced an explicit "How To Play" section titled **"LIFT AND
THROW:"** on page 15 — the exact English name the disassembly-confirmed
mechanism had been missing, closing a long-standing item with zero live
capture and zero `re-oracle` escalation needed. The three actions the
manual named (lift / throw forward / gently drop) even matched, one-for-one,
three already-disassembled player-animation-id branches that had no a
priori reason to align — a real cross-check, not a coincidence.

**The fix, cheap and worth doing before trusting any "manual checked, found
nothing" line**: run `pdfinfo <file>.pdf` and `pdftotext -layout <file>.pdf -`
first. If `pdftotext` returns non-trivial text, a grep-based check is valid
evidence. If it returns empty (or the `Producer`/`Creator` field says
something like "Image Conversion Plug-in"), the document has never actually
been searched — it has to be read as images (`Read` with a `pages` range)
before any negative claim about its contents can be trusted, and any
existing "checked, found none" claim against it should be treated as
unverified rather than as a settled negative.

**Broader ordering lesson**: when hunting for a mechanic's *official* name
and the game's own data ships no name table for it, an official manual's
"How To Play"/controls section is a first-class, cheap oracle worth checking
early — before spending a round on a sibling platform's stripped debug
strings or an exhaustive in-game text-corpus scan, not only after those come
up empty.
