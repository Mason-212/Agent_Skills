---
name: ocrstatus
description: Show ocr-to-md watcher status and the pending OCR Inbox queue
---

# OCR Status

## When to Use

- The user invokes `/ocrstatus`
- The user asks what OCR is running, what is in the queue, or whether inbox photos are done

This skill is **read-only**. Do not start, stop, or reconfigure the watcher.

## Operating Procedure

1. **Run the status script.** Prefer the installed copy, then the repo copy:

   ```
   bash ~/.cursor/skills/ocrstatus/resources/ocrstatus.sh
   ```

   If that path does not exist, run:

   ```
   bash ~/dev/Agent_Skills/skills/ocrstatus/resources/ocrstatus.sh
   ```

2. **Present the script output** to the user. Keep the same sections:
   - Watcher / process / currently running page
   - Queue (inbox images with no sibling `.md` yet)
   - Recently finished pages

3. **If the script is missing**, gather the same facts by hand:
   - `launchctl print gui/$(id -u)/com.user.ocr-to-md` — watcher loaded/running
   - `pgrep -af 'watch-inbox|ocr-to-md |glm_ocr.py'` — live processes
   - Scan `$HOME/school/**/OCR Inbox` for image files that do not have a sibling `.md`
   - Tail `$HOME/Library/Logs/ocr-to-md.log` for the current `◆ OCR` job and last `wrote` lines

4. **Interpret briefly.** One or two sentences is enough, for example:
   - Watcher running, now OCR-ing `Science/Living Earth/OCR Inbox/IMG_3389.heic`, 4 waiting
   - Watcher running and idle, queue empty
   - Watcher not running — mention `/ocr-to-md setup` to repair it, but do not run setup unless the user asks

## Queue rules

An image is **queued** when it is under an `OCR Inbox` folder, has an image extension (`.heic`, `.jpg`, `.png`, …), has no sibling `.md`, and is not listed in `~/Library/Application Support/ocr-to-md/skipped-images`.

The watcher processes **one page at a time**. The page in the current `ocr-to-md` command line is **running**, not queued.

## Important Constraints

- **Do not** start OCR jobs, pass `--force`, or edit inbox files.
- **Do not** dump full OCR markdown or the entire log unless the user asks.
- **Do not** treat this as `/ocr-to-md` or `/pushschool`.
