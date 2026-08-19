# Sibling games in one engine family sharing an asset *format* doesn't mean they share the *container*

**When it bites:** a task brief or prior doc says two games are "the same
engine, same file family" (shared G1T/G1M/WTB/etc. asset formats already
solved for one of them) and asks you to check whether a specific *archive/
container* format (LINKDATA, PAK, WAD, ...) is "probably the same, just
unverified" — before you've grepped the second game's actual file tree for
that container's filename/magic.

Chimera (Koei Tecmo Musou engine): the brief assumed Fire Emblem Warriors
(2017) uses the same `LINKDATA_*.BIN` archive layout as Fire Emblem Warriors:
Three Hopes (2022), hedged only as "not yet verified." A recursive filename
search (`find <romfs> -iname '*linkdata*'`) across the entire 2017 base
romfs returned **zero matches** — there is no LINKDATA archive in that
game's data at all. The two games do share the G1T texture format and (by
internal chunk-tag evidence) the G1M model format, and both decode with the
same `g1t.ts`. But the 2017 game stores those G1T-bearing assets as
individual per-character "pack" files scattered directly through the
directory tree, not inside any top-level indexed archive — a completely
different container architecture, not a header variant.

The generalizable point: "same engine family" is real and valuable evidence
for shared *content* formats (texture/model/animation codecs), which is
exactly why cross-referencing sibling projects/games is worth doing first
(see the Prior-art corpora table). It is much weaker evidence for shared
*archive/container* formats, because studios routinely change their asset
*packaging* pipeline between titles/years even when the underlying content
codecs carry over unchanged (they're usually different tools/teams: content
exporters vs. build/packaging scripts). Treat "does the container exist at
all in this game's data" as a five-second, zero-cost check
(`find`/`grep -r` for the expected filename or magic) to run **before**
writing a byte-level comparison plan for "confirm the header matches" — a
plan that's moot if the container isn't present to begin with. If the
premise fails this fast, it usually only strengthens the case for the
content-level formats being shared (which don't depend on any particular
container), so the two aren't wasted work in different directions — you
still know where to point the shared decoder, just via a different content-
discovery route (a magic-byte scan for the content format directly, see
`magic-byte-scan-bypasses-container-reverse-engineering.md`).
