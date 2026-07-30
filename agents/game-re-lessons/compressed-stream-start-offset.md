# Compressed streams may not start where the directory ends

**When it bites:** output looks "scrambled" right after what seemed like a clean directory/header parse.

A 214-byte raw table sat between the directory and the RLE stream in one
format; decoding from the directory's end desynced everything and looked
exactly like a bitplane-alignment bug. If output is scrambled, suspect the
stream start offset before you suspect the pixel layout.
