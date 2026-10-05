# A "was this resource ever referenced" census built from a downstream named/paired/joined output can hide real references the raw operand census already found

**When it bites:** deciding whether a TOC slot/resource id/asset is "genuinely
unreferenced" by querying the output of a higher-level join or pairing
function (a portrait-to-speaker name table, a resolved id→name map, any
"decoded result" cache) instead of the raw literal-push/operand census that
feeds it — especially across several rounds/sessions, where each re-check
re-runs the same downstream query and re-confirms the same "still
unreferenced" list without ever re-deriving it from the raw pushes again.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), `vp1psx-portrait-scene-
script-join`: a scene-script portrait mechanism was fully cracked (opcode 168
pushes a literal TOC slot, consumed two calls later) and a 1,800-literal
census of every such push was built and verified byte-exact. But the
*naming* helper built on top of it (`readScenePortraitLines`) only emitted a
speaker pairing when the specific consumer instruction it modeled (`CALL
0x3E2`, the shared library's text-window call) followed the push — and a
subset of rooms drew their dialogue with a *sibling* opcode family
(immediate-form `TEXTWIN`, several related opcodes) that the helper never
recognized as a text-showing instruction at all. The result: 8 real,
already-pushed portrait references — sitting inside the existing 1,800-
literal census the whole time — produced no name, so the "reference"
question (itself entirely separate from "what's its name") was answered by
reading the *named* output's gaps as "unreferenced," rather than by checking
the raw push set directly. This survived multiple "hardened negative"
write-ups across several rounds, because every re-check re-ran the same
named-output query instead of re-deriving the reference set from scratch.

**Fix:** a "was resource X ever referenced" question has its own oracle — the
raw literal-push/operand/opcode-argument census — and that oracle must be
queried directly, not inferred from whether a *different*, narrower-scoped
downstream function (built to answer a related but stricter question, like
"and what's it called") happened to produce output for that id. Before
writing up (or re-confirming) a "genuinely unreferenced" verdict, re-run the
raw census fresh and cross-check its result set against the named output's
gaps — if the raw census finds hits the named output doesn't explain, the
gap is in the naming/pairing model's own consumer coverage, not in whether
the resource is referenced. This is the census-completeness sibling of
`runtime-valued-script-operand-is-usually-a-parameter.md` (which covers a
different but related trap: a single ambiguous-looking operand read being
misclassified as "computed at runtime" when it's really a script-local
function's own parameter, reachable only by tracing that function's call
sites) — both failures look like solid negatives from the vantage point that
produced them, and both are cracked by going back to the raw push/argument
data instead of trusting an intermediate abstraction's own scope.
