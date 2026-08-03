# A same-named cross-port asset doesn't have to match colour

**When it bites:** a bug report (or your own eyeballing) says platform B's render of a character/asset "looks badly wrong" because it doesn't match platform A's colours for the same-named file, and platform A is treated as automatically-correct ground truth.

Two ports of the same game can and do use **deliberately different palettes**
for the same character, especially when the two platforms have very
different colour budgets. Confirmed on Dune (Cryo, 1992): the DOS VGA port's
`baro.hsq` (Baron Harkonnen) and `hark.hsq` (a Harkonnen soldier) decode to
dark-red/maroon flesh and solid violet/purple armour respectively — nothing
resembling the Amiga port's orange-tan skin and orange-brown cloak for the
same two characters. Structural analysis proved the DOS decode was byte-exact
and fully self-contained (every sprite pixel index fell inside the file's own
declared palette block; a sibling file with an *identical* block shape,
`chan`, decoded to correct, recognisable colours, ruling out a parsing bug).
The actual explanation: DOS's 256-colour palette let the artists give the
Baron and a generic Harkonnen soldier visually distinct colour schemes;
Amiga's 32-colour budget forced both characters to share one palette bank
(confirmed: Amiga's `baro.hsq` and `hark.hsq` have byte-identical 15-colour
palette blocks). Two real screenshots of the actual released DOS game
(sourced from an abandonware site's screenshot gallery, not this project's
own renders) confirmed the "wrong-looking" DOS decode was correct all along
— the bug report's premise (Amiga colour = required DOS colour) was false.

**Diagnostic tell:** if no permutation of the suspect palette's byte order
(R,G,B / B,G,R / G,R,B / …) can produce the "expected" hue family — e.g. a
ramp where two channels are always close together and one is always low
(a magenta/purple-family shape) fundamentally cannot become a ramp with
three well-separated channels (an orange-family shape) under any relabelling
— the file's declared values are what they are; second-guess the *reference
platform assumption*, not the byte order, before spending more effort on
"decode bugs" the data structurally rules out.

**Before touching code:** if the target platform's data structurally
confirms (self-contained pixel-index coverage, byte-exact block closure,
correct decode on a shape-identical sibling file) and only the *colour*
looks surprising next to a different platform's version of the same
character, look for that platform's *own* screenshots (community
screenshot galleries, longplay stills, abandonware sites) before assuming
a bug and rewriting the palette-merge/donor logic. A real screenshot of the
actual platform in question is a stronger oracle than a sibling port's
render for questions of platform-specific artistic choice — the sibling
port is ground truth for *structure*, not necessarily for *colour*.
