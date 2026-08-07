# Extending a first-match-wins alias/rule table with a secondary discriminator needs the specific rule listed before its shared-key fallback

**When it bites:** a project's display-name/alias system (or any
declarative "first rule whose key matches wins" lookup table keyed by a
single structural identity value — a bone/joint signature, a content hash,
a cluster id) needs to express two *different* names/results for two
different concrete instances that happen to share the *same* key value —
not a new key you can just add a row for, because the existing schema has
no way to say "this key, but only when this other condition also holds."

Confirmed on Drakengard 3 (PS3, `flower`): the character-alias system
(`character-aliases.ts`) keyed every rule purely on `boneSignature` (one
structural skeleton/rig = one character identity), which held for every
character found through several sessions — even multi-form characters
(Zero's damage-state rigs, Cerberus's head/body sub-rigs, Abdiel's
tri-body/tri-head phases) always had a *different* joint set, hence a
different `boneSignature`, per name. The first real counterexample:
two named boss forms (Gabriel, and Zophiel — his own transformed second
phase per the game's own class hierarchy) share the **identical**
`boneSignature` — the exact same rig, reused with different
textures/content for the two forms, so no new key existed to hang a second
rule on.

**The fix, and its trap**: add an optional secondary discriminator field to
the rule (here, `nameContains` — a substring the manifest entry's own
object name must also contain) and thread a second parameter through the
lookup function for it. This is straightforward. The trap is purely about
*array order*: a `.find()`-based first-match lookup means the
discriminator-scoped rule **must** be listed before the broader,
unscoped fallback rule that shares the same primary key — otherwise the
general rule (which matches unconditionally on the shared key) shadows the
specific one and always wins, silently. This is easy to get right by
construction while writing the new rules (put the more specific one
first) and easy to get *silently* wrong later if a rule table gets
reordered, alphabetized, or merged by someone who doesn't know the
first-match convention carries meaning. Write a dedicated test asserting
the ordering invariant directly (iterate the table, for every
discriminator-scoped rule assert no *earlier* same-key rule lacks a
discriminator) — a functional "does lookup X resolve to Y" test alone can
pass today and silently break the moment the table is reordered for an
unrelated reason.
