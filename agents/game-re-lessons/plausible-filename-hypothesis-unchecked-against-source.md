# A plausible-sounding filename/extension guess about a file's role can be flatly wrong — check the loader source before it ossifies into a doc claim

**When it bites:** a doc states what a file/resource *is* based on its
extension, name, or size alone ("almost certainly X, not a resource file"),
with no code-level check, and a reference reimplementation's source is
already available (already cloned, already read for other formats in the
same corpus) but wasn't grepped for this specific filename/extension.

A confident-sounding naming inference is not evidence, even when it feels
obviously right and even when it's cheap to state. The fix, when a
reference engine's source exists, is a single grep for the extension or
filename pattern in its resource-loading code — often faster than writing
the sentence that guesses instead.

Confirmed on Lands of Lore's `DATA/NN.TLK` files (`crawl` project, Kyra
engine): a prior pass recorded "30 `.TLK` files, up to 29 MB each —
almost certainly CD-audio/speech track data ('TLK' = 'talk'), not Kyra PAK
resources; not investigated" — a reasonable-sounding guess for a
CD-ROM-era RPG with voice acting. ScummVM's `engines/kyra/engine/lol.cpp`
(`LoLEngine::loadTalkFile`) refuted it in one grep: `.TLK` files are
loaded with the *exact same* `_res->loadPakFile()`/`unloadPakFile()` calls
used for every other `.PAK` archive in the engine — ordinary Kyra PAK
containers, not raw audio. Extracting the smallest one and parsing it with
the project's existing, already-verified PAK-directory parser (unmodified)
confirmed it byte-exact: a single `00000.VOC` (Creative Voice File) entry,
directory offset + size landing exactly on the file's own end. What had
been logged as "an audio format question, out of scope" was actually
"already-decodable with existing code, zero new work" — the wrong guess
had been costing nothing to *state* but would have cost an entire format
investigation to *un-guess* later if never checked.

The general move: before writing a filename/extension-based content-type
claim into a doc — especially one that closes off further investigation
("not a resource file", "out of scope", "CD-audio, skip") — spend the one
grep against the reference engine's resource-loading code if that source
is already available. This is a narrower, cheaper-to-apply case of
`romhacking-community-tools-first.md`'s broader "read the source before
guessing" theme, specifically for the moment a doc is about to assert a
file's *category* rather than its byte layout.
