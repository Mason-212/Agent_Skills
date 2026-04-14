---
name: gws-google-docs
description: Use the gws CLI to search, read, create, and import Google Docs across Drive and shared drives.
---

# Google Docs and Drive via `gws`

Use this skill when the user wants to search Drive for Google Docs, read a document, create a new Google Doc, import Markdown or HTML into Docs, or write content into a doc through the already-configured `gws` CLI.

## Rules

1. Assume `gws` auth is already configured unless the command proves otherwise.
2. Before executing a write operation, confirm with the user. This includes:
   - `gws docs documents create`
   - `gws docs +write`
   - `gws docs documents batchUpdate`
   - `gws drive files create`
   - `gws drive files update`
   - `gws drive files delete`
   - any permission change or deletion
3. If a method shape is unclear, inspect it first with `gws <service> --help` or `gws schema <service.resource.method>`.
4. Prefer plain-text export when the user wants the actual document contents in chat. Prefer `docs.documents.get` when the user needs structured document JSON.
5. `gws drive files export --output` must point inside the current working directory. Do not write to `/tmp` or other paths outside the workspace unless `gws` explicitly allows it.
6. When consuming `gws` output programmatically, parse JSON defensively because stdout or stderr can include extra lines such as keyring backend notices before the JSON payload.
7. If the user wants to import Markdown, inspect supported import formats first with `gws drive about get --params '{"fields":"importFormats"}'`. In this workspace, Drive advertises both `text/markdown` and `text/x-markdown` as importable to Google Docs.
8. Direct Markdown import can still be flaky or can drop diagrams. For Markdown files with diagrams or local images, prefer HTML import with embedded PNG data URIs, then fix the title paragraph style with `documents batchUpdate`.
9. Split large create/import/verify flows into multiple short commands instead of one large blocking heredoc so the terminal does not appear stuck.

## Shared drive behavior

Shared drives are not a separate `spaces` value. To make shared drives searchable, use Drive search with:

- `supportsAllDrives: true`
- `includeItemsFromAllDrives: true`
- `spaces: "drive"`

Use one of these scopes:

- `corpora: "allDrives"` to search My Drive plus shared drives
- `corpora: "drive"` with `driveId` to search one specific shared drive

If the user names a shared drive but not its ID, resolve it first with `gws drive drives list`.

## Recipes

### 1. Search Google Docs across My Drive and shared drives

Use `drive.files.list`, not the Docs API, for discovery.

```bash
gws drive files list --params "$(cat <<'JSON'
{
  "q": "mimeType='application/vnd.google-apps.document' and trashed=false and name contains 'Discovery'",
  "pageSize": 20,
  "supportsAllDrives": true,
  "includeItemsFromAllDrives": true,
  "corpora": "allDrives",
  "spaces": "drive"
}
JSON
)"
```

To search by document text instead of title, change the query to use `fullText contains '...'`.

### 2. Find shared drives, then search one specific shared drive

```bash
gws drive drives list --params "$(cat <<'JSON'
{
  "q": "name contains 'Analytics'",
  "pageSize": 20
}
JSON
)"
```

Then narrow the file search to one shared drive:

```bash
gws drive files list --params "$(cat <<'JSON'
{
  "q": "mimeType='application/vnd.google-apps.document' and trashed=false",
  "pageSize": 20,
  "supportsAllDrives": true,
  "includeItemsFromAllDrives": true,
  "corpora": "drive",
  "driveId": "SHARED_DRIVE_ID",
  "spaces": "drive"
}
JSON
)"
```

### 3. Retrieve a document as readable text

```bash
gws drive files export --params "$(cat <<'JSON'
{
  "fileId": "DOC_ID",
  "mimeType": "text/plain"
}
JSON
)" --output gws-doc.txt
```

After export, read `gws-doc.txt` and summarize or transform it for the user.
`gws` may reject output paths outside the current working directory.

### 4. Retrieve a document as structured JSON

```bash
gws docs documents get --params "$(cat <<'JSON'
{
  "documentId": "DOC_ID"
}
JSON
)"
```

Use this when the user needs document structure or API-level metadata rather than plain text.

### 5. Create a new blank Google Doc

```bash
gws docs documents create --json "$(cat <<'JSON'
{
  "title": "Document Title"
}
JSON
)"
```

Parse the returned `documentId` from the JSON response before the next step.

### 6. Append text to a document

```bash
gws docs +write --document "DOC_ID" --text "$(cat <<'TEXT'
Hello from Cascade.

This is plain text appended to the end of the document.
TEXT
)"
```

Notes:

- `+write` appends plain text at the end of the doc.
- Markdown syntax is written as literal text, not rich Docs formatting.
- For richer editing, use `documents batchUpdate`.

### 7. Insert structured content with `batchUpdate`

```bash
gws docs documents batchUpdate --params "$(cat <<'JSON'
{
  "documentId": "DOC_ID"
}
JSON
)" --json "$(cat <<'JSON'
{
  "requests": [
    {
      "insertText": {
        "location": {
          "index": 1
        },
        "text": "Title\n\nFirst paragraph.\n"
      }
    }
  ]
}
JSON
)"
```

Use `batchUpdate` when the user needs precise insertion, formatting, or multiple edits in one request.

### 8. Check which source formats Drive can import into Google Docs

```bash
gws drive about get --params '{"fields":"importFormats"}'
```

Use this before a new import flow. In this workspace, Drive advertises both `text/markdown` and `text/x-markdown` as importable to `application/vnd.google-apps.document`.

### 9. Import Markdown directly when the source is mostly text

```bash
gws drive files create --params "$(cat <<'JSON'
{
  "fields": "id,name,webViewLink,mimeType"
}
JSON
)" --json "$(cat <<'JSON'
{
  "name": "Document Title",
  "mimeType": "application/vnd.google-apps.document"
}
JSON
)" --upload "notes.md" --upload-content-type "text/x-markdown"
```

If `text/x-markdown` returns `internalError`, retry with `text/markdown`.
This path is acceptable for text-heavy docs, but it may omit local diagrams or SVG-backed image refs.
After import, fetch the doc with `docs.documents.get`, find the paragraph whose text matches the H1, and set that paragraph to `TITLE` with `documents batchUpdate`:

```bash
gws docs documents batchUpdate --params "$(cat <<'JSON'
{
  "documentId": "DOC_ID"
}
JSON
)" --json "$(cat <<'JSON'
{
  "requests": [
    {
      "updateParagraphStyle": {
        "range": {
          "startIndex": START_INDEX,
          "endIndex": END_INDEX
        },
        "paragraphStyle": {
          "namedStyleType": "TITLE"
        },
        "fields": "namedStyleType"
      }
    }
  ]
}
JSON
)"
```

Replace `startIndex` and `endIndex` with the actual range returned for the paragraph whose text matches the H1.

### 10. Import Markdown with local diagrams or images

Use this when the Markdown contains local image refs such as `![][image1]` and the user wants diagrams preserved.

1. Resolve Markdown image refs to local files.
2. Prefer PNG, JPEG, or GIF. If the source ref points to an `.svg` and a sibling `.png` exists, use the PNG.
3. Generate an HTML file that embeds the images as `data:` URIs. A short local Python helper is fine:

```bash
python3 - <<'PY'
import base64
import mimetypes
import pathlib

# List all resolved image paths here
image_paths = [
    "images/diagram.png",
    # Add all resolved image refs from the Markdown source
]

img_tags = []
for p in image_paths:
    img = pathlib.Path(p)
    mime = mimetypes.guess_type(img.name)[0] or "image/png"
    data = base64.b64encode(img.read_bytes()).decode("ascii")
    img_tags.append(f'<p><img src="data:{mime};base64,{data}" /></p>')

body = "<h1>Document Title</h1>\n" + "\n".join(img_tags)
pathlib.Path("doc.import.html").write_text(
    f"<html><body>{body}</body></html>",
    encoding="utf-8",
)
PY
```

Extend the `image_paths` list with every resolved local image ref from the Markdown source.

4. Import the generated HTML:

```bash
gws drive files create --params "$(cat <<'JSON'
{
  "fields": "id,name,webViewLink,mimeType"
}
JSON
)" --json "$(cat <<'JSON'
{
  "name": "Document Title",
  "mimeType": "application/vnd.google-apps.document"
}
JSON
)" --upload "doc.import.html" --upload-content-type "text/html"
```

5. Post-process the H1 paragraph to `TITLE` with `documents batchUpdate`.
6. Verify diagrams with `docs.documents.get`. Imported images should appear in `inlineObjects` or `positionedObjects`.

Do not rely on `insertInlineImage` for local-only assets. The Docs API expects a public URI for that path, while HTML import with embedded data URIs preserves local diagrams without publishing them.

## Suggested execution order for typical requests

### Read an existing doc when only a name or topic is known

1. Search with `gws drive files list`.
2. If needed, resolve a specific shared drive and narrow with `driveId`.
3. Export the chosen doc to plain text with `gws drive files export`.
4. Read the exported file locally and return the content or summary.

### Create a new blank doc and write plain text into it

1. Confirm the write with the user.
2. Run `gws docs documents create`.
3. Extract `documentId` from the response.
4. Run `gws docs +write` or `gws docs documents batchUpdate`.
5. Return the new document ID and any relevant metadata from the response.

### Import a Markdown doc without diagrams

1. Confirm the write with the user.
2. Optionally inspect import formats with `gws drive about get`.
3. Import the `.md` file with `gws drive files create` and `--upload-content-type text/x-markdown`.
4. If `text/x-markdown` fails with `internalError`, retry with `text/markdown`.
5. Run `gws docs documents get`.
6. Find the paragraph whose text matches the H1 and convert it to `TITLE` with `documents batchUpdate`.
7. Return the new document ID and link.

### Import a Markdown doc with local diagrams or images

1. Confirm the write with the user.
2. Resolve image refs to local files and switch SVG refs to PNG when possible.
3. Generate HTML with embedded image data URIs.
4. Import the HTML with `gws drive files create --upload-content-type text/html`.
5. Run `gws docs documents get` to verify the title paragraph style and image objects.
6. Export to a local text file if you need to spot check the content in the IDE.
7. Return the new document ID and link.

## Good defaults

- Prefer `pageSize` between `10` and `50`.
- Always include `trashed=false` in Drive search unless the user explicitly wants trashed items.
- Prefer `corpora: "drive"` plus `driveId` when the target shared drive is known.
- Use local export files such as `gws-doc.txt` when you need to inspect or summarize the content inside the IDE.
- Check `gws drive about get --params '{"fields":"importFormats"}'` before a new import flow.
- Try `text/x-markdown` first for direct Markdown import, then retry with `text/markdown` if Google returns `internalError`.
- Prefer HTML import with embedded PNG data URIs when diagrams or local images matter.
- After any import, verify that the H1 paragraph was converted to Google Docs `TITLE`.
- Split long create/import/verify flows into separate commands.
