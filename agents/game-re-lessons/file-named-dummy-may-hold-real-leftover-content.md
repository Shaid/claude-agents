# A file conventionally named "dummy"/filler on a game disc may hold real, well-formed leftover content

**When it bites:** a disc/archive contains a file with a generic
padding-suggesting name (`DUMMY.DMY`, `PADDING.BIN`, `FILLER.DAT`) and/or a
size that looks like it exists only to round out a disc-mastering layout —
before writing it off unread as inert padding, check its actual bytes.

The filename and the mastering-convenience narrative are both real and
common (many PS1/PS2 discs do ship padding files to hit a required track
size), but "this file's *purpose* on the disc is padding" says nothing
about whether the disc-mastering tool actually zero-filled it or just
reused whatever leftover build data happened to be lying around, since only
the file's *size* mattered for layout purposes. A padding file is exactly
as likely to be stale/discarded real asset data as it is to be zeros — the
mastering process doesn't care which, and the filename gives no signal
either way.

Confirmed on Parasite Eve II (PSX, `~/Development/parasite`):
`DUMMY.DMY` (50,667,520 bytes, byte-identical on both discs) is
conventionally exactly the kind of file this pitfall describes — but its
first bytes are a real, well-formed PSX STR-v2 MDEC video-sector header
(valid magic, sane `chunksInFrame`/`frameNumber`/`quantScale`/`version`
fields, not noise that coincidentally starts with the right magic byte),
and the file is **100.0% non-`0xFF` content** for all but its final ~2 KB —
dense, structured data start to finish, not "mostly blank with a bit of
junk." The one substantive resolution field present (`width=256,
height=176`) doesn't match any confirmed-shipped movie's resolution in
either Parasite Eve title, consistent with unused/cut content rather than
an in-use asset — but the point stands regardless of what it turns out to
be: this file cannot be dismissed as inert padding from its name and role
alone.

**Fix:** run the same first-look checks on a "dummy"/filler-named file that
you'd run on any unidentified file — magic-byte scan, entropy/histogram
over its full stored length (not just a tail sample, see
`padded-file-tail-describes-padding-not-content.md` for the inverse
mistake), a plain strings pass. A file's *name* and its *disc-layout role*
are both weak evidence about its *content* — treat "labeled/used as
padding" as license to skip decoding it only after a real byte-level check
comes back genuinely blank (all-zero, or a single repeated filler byte),
not before. This is the whole-file counterpart to
`no-traced-reader-region-is-not-proof-of-filler.md` (which covers an
unread *region* inside an otherwise-traced binary) — here the "no reason to
read it" signal comes from the file's name/mastering role rather than an
incomplete loader trace, but the fix is the same: check before you file it
away.
