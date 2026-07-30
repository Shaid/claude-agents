# Indexed sub-structures can be locally indexed per-chunk, not one shared pool

**When it bites:** a multi-part format's vertex/element indices look small enough that "one shared pool" seems necessary but resolving against it produces garbage.

A multi-part icon/mesh looked like it needed one big shared vertex table
because every chunk's edge indices were small. Actually each chunk carried
its own tiny vertex table immediately before its own edge list, with indices
always restarting at 0 per chunk. When "index into shared pool" produces
garbage, test "does each chunk own its table" before concluding the data is
corrupt.
