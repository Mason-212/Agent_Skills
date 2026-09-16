---
name: ocr-check
description: Show OCR queue order and current job. Use when user says /ocr-check or OCR check.
---

# OCR Check

## When to Use

- The user invokes `/ocr-check`, `/OCR check`, or `OCR check`
- The user asks which images are waiting for OCR and in what order
- The user asks what page is currently being processed

This skill is **read-only**. Do not start, stop, kill, or requeue OCR jobs.

## Operating Procedure

1. **Run the check script.** Prefer the installed copy, then the repo copy:

   ```
   bash ~/.cursor/skills/ocr-check/resources/ocr-check.sh
   ```

   If that path does not exist, run:

   ```
   bash ~/dev/Agent_Skills/skills/ocr-check/resources/ocr-check.sh
   ```

2. **Present the script output** to the user. Keep the same sections:
   - Now processing (the live `ocr-to-md` page, or idle)
   - Queue order (next up first; items marked `[back of queue]` were sent there by `/ocr-terminate`)

3. **If the script is missing**, gather the same facts by hand:
   - `pgrep -af 'ocr-to-md |glm_ocr.py'` — the page currently running
   - Scan `$HOME/school/**/OCR Inbox` for image files with no sibling `.md`
   - Read `$HOME/Library/Application Support/ocr-to-md/deferred-images` — those paths go last

4. **Interpret briefly.** One sentence is enough, for example:
   - Now OCR-ing `IMG_3389.heic`; 3 waiting, next is `IMG_3390.heic`
   - Watcher idle, queue empty

## Queue rules

An image is **queued** when it is under an `OCR Inbox` folder, has an image extension, has no sibling `.md`, and is not listed in `~/Library/Application Support/ocr-to-md/skipped-images`.

The watcher processes **one page at a time**. The page in the current `ocr-to-md` command line is **running**, not waiting.

Images listed in `~/Library/Application Support/ocr-to-md/deferred-images` stay at the **back of the queue** until every non-deferred waiting page is done.

## Important Constraints

- **Do not** start OCR jobs, pass `--force`, kill processes, or edit inbox files.
- **Do not** treat this as `/ocr-terminate`, `/ocr-to-md`, or `/pushschool`.
- To kill a named page and move it to the back, use `/ocr-terminate`.
