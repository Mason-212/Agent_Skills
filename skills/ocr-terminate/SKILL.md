---
name: ocr-terminate
description: Kill named OCR job and send it to back of queue. Use for /ocr-terminate.
---

# OCR Terminate

## When to Use

- The user invokes `/ocr-terminate`, `/OCRTerminate`, `/OCR Terminate`, or `OCR/Terminate`
- The user names a page on the OCR queue (filename, stem, or queue number) and wants that OCR killed and sent to the back

## Usage

```
/ocr-terminate IMG_3389.heic
/ocr-terminate IMG_3389
/ocr-terminate 2
```

The rest of the user message after the command is the target. Queue numbers match `/ocr-check` (1 = next up).

## Operating Procedure

1. **Parse the target** from the user message. Strip the command prefix (`/ocr-terminate`, `/OCRTerminate`, `OCR/Terminate`, and similar). What remains is the name.

2. **If the name is missing**, run `/ocr-check` (the `ocr-check.sh` script) and ask which page to terminate. Do not guess.

3. **Run the terminate script** with that name. Prefer the installed copy, then the repo copy:

   ```
   bash ~/.cursor/skills/ocr-terminate/resources/ocr-terminate.sh "NAME"
   ```

   If that path does not exist, run:

   ```
   bash ~/dev/Agent_Skills/skills/ocr-terminate/resources/ocr-terminate.sh "NAME"
   ```

   Pass the user's name as a **single argument**. Do not interpolate it into a shell string beyond that argv.

4. **Present the script output** to the user (what was killed or moved, then the new queue order).

5. **If the script is missing**, stop. Do not invent a kill command. Tell the user the skill script is not installed.

## What the script does

- Resolves the name to one inbox image that is running or waiting
- Writes that image to `~/Library/Application Support/ocr-to-md/deferred-images` (moves it to the end if it was already there)
- If that image is the live OCR job: stops `ocr-to-md` and `glm_ocr.py` for it, **not** `watch-inbox` and **not** Ollama
- The watcher then skips it until every other waiting page is done, then retries it last

## Important Constraints

- **Do not** kill `watch-inbox`, `ollama`, or unrelated processes.
- **Do not** delete the image or its folder. Sending to the back is defer-only.
- **Do not** pass `--force` or start a new OCR job.
- If several images match the name, show the matches and stop. Do not kill more than one.
- If the named page is waiting (not running), still send it to the back; there is no process to kill.
- This is not `/ocr-check` (read-only) and not `/ocr-to-md setup`.
