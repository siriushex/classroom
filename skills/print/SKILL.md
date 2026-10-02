---
name: print
description: Type user-approved text into the currently focused macOS app one character at a time. Use only for explicit requests to emulate keyboard input locally.
---

# Print text into the active app

Use this skill only when the user explicitly asks to type text through the local
keyboard. It is available as `$print`.

Before running the helper, identify the exact target app or field and obtain
confirmation immediately before text is sent. Do not select a destination,
open a page, submit a form, or type sensitive information unless the user has
authorized that exact transfer.

Run a dry check first when practical:

```bash
python3 ./scripts/type_text.py \
  --text "Text to type" --dry-run
```

For multi-line text or non-Latin characters, write the approved text to a UTF-8
file and use `--file` rather than placing it on the command line:

```bash
python3 ./scripts/type_text.py \
  --file /absolute/path/to/text.txt --delay 5 --interval 0.03
```

The script pastes one character per macOS System Events action and presses Return
for each newline. It restores the previous text clipboard at the end and requires
Accessibility access for the terminal or Python. Control-C stops the run.
The default mode types into the current field. Optional `--app`, paired
`--click-x`/`--click-y`, and `--document-end` can activate an app, click and move
to the document end. Use these options only after confirming the exact target.
The helper does not select existing text or submit a Classroom assignment.
