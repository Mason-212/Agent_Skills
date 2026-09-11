#!/usr/bin/env bash
# Report ocr-to-md watcher state and the pending OCR Inbox queue.
set -euo pipefail

SCHOOL_ROOT="${SCHOOL_ROOT:-$HOME/school}"
LOG_PATH="${OCR_LOG_PATH:-$HOME/Library/Logs/ocr-to-md.log}"
SKIP_FILE="${OCR_SKIP_FILE:-$HOME/Library/Application Support/ocr-to-md/skipped-images}"
LABEL="com.user.ocr-to-md"
UID_NUM="$(id -u)"

is_image() {
  local lower
  lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    *.png|*.jpg|*.jpeg|*.webp|*.heic|*.heif|*.tif|*.tiff|*.gif|*.bmp) return 0 ;;
    *) return 1 ;;
  esac
}

is_skipped() {
  local img="$1" base
  [[ -f "$SKIP_FILE" ]] || return 1
  base="$(basename "$img")"
  grep -Fxq -- "$base" "$SKIP_FILE" || grep -Fxq -- "$img" "$SKIP_FILE"
}

rel_school() {
  local path="$1"
  if [[ "$path" == "$SCHOOL_ROOT/"* ]]; then
    printf '%s\n' "${path#"$SCHOOL_ROOT"/}"
  else
    printf '%s\n' "$path"
  fi
}

echo "OCR Status"
echo "=========="
echo

# --- Watcher / launchd -----------------------------------------------------
launch_state="not loaded"
launch_pid=""
if launchctl print "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1; then
  launch_state="$(launchctl print "gui/${UID_NUM}/${LABEL}" 2>/dev/null | awk -F ' = ' '/^[[:space:]]*state = / { print $2; exit }')"
  launch_pid="$(launchctl print "gui/${UID_NUM}/${LABEL}" 2>/dev/null | awk '/pid = / { print $3; exit }')"
fi

ps_dump="$(ps -ax -o pid=,command= 2>/dev/null || ps aux)"
watch_line="$(printf '%s\n' "$ps_dump" | grep -E 'watch-inbox' | grep -v grep | head -1 || true)"
ocr_line="$(printf '%s\n' "$ps_dump" | grep -E 'scripts/ocr-to-md |/ocr-to-md ' | grep -v -E 'watch-inbox|ocrstatus|grep' | head -1 || true)"
glm_line="$(printf '%s\n' "$ps_dump" | grep -E 'glm_ocr.py' | grep -v grep | head -1 || true)"
ollama_ok="no"
if curl -sf --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  ollama_ok="yes"
fi

printf 'Watcher:  %s' "${launch_state:-unknown}"
if [[ -n "$launch_pid" ]]; then
  printf ' (launchd pid %s)' "$launch_pid"
fi
echo
if [[ -n "$watch_line" ]]; then
  printf 'Process:  %s\n' "$watch_line"
else
  echo "Process:  watch-inbox is not running"
fi

current_image=""
if [[ -n "$ocr_line" ]]; then
  current_image="${ocr_line##*ocr-to-md }"
  current_image="${current_image#--force }"
  current_image="${current_image%% }"
  printf 'Running:  %s\n' "$(rel_school "$current_image")"
else
  echo "Running:  idle (no page in progress)"
fi

if [[ -n "$glm_line" ]]; then
  echo "Engine:   glm-ocr is active"
else
  echo "Engine:   glm-ocr is idle"
fi
printf 'Ollama:   %s\n' "$ollama_ok"

# Last useful log line about the current page
if [[ -f "$LOG_PATH" ]]; then
  last_progress="$(awk '
    /◆ OCR / { current=$0; next }
    /✓ done|✗ failed|✗ giving up/ { current="" }
    { if (current != "") last=$0 }
    END { if (last != "") print last }
  ' "$LOG_PATH" 2>/dev/null || true)"
  if [[ -n "$last_progress" ]]; then
    printf 'Progress: %s\n' "$(printf '%s' "$last_progress" | tr -d '\033' | sed -E 's/\[[0-9;]*m//g')"
  fi
  echo "Log:      $LOG_PATH"
fi

echo

# --- Queue -----------------------------------------------------------------
pending=()
while IFS= read -r -d '' inbox; do
  while IFS= read -r -d '' img; do
    is_image "$img" || continue
    is_skipped "$img" && continue
    md="${img%.*}.md"
    if [[ -f "$md" ]]; then
      continue
    fi
    pending+=("$img")
  done < <(find "$inbox" -type f -print0 2>/dev/null)
done < <(find "$SCHOOL_ROOT" -type d -name 'OCR Inbox' -print0 2>/dev/null)

queued=()
for img in "${pending[@]+"${pending[@]}"}"; do
  if [[ -n "$current_image" && "$img" == "$current_image" ]]; then
    continue
  fi
  queued+=("$img")
done

printf 'Queue:    %s waiting\n' "${#queued[@]}"
if [[ ${#queued[@]} -eq 0 ]]; then
  echo "  (empty)"
else
  for img in "${queued[@]}"; do
    printf '  - %s\n' "$(rel_school "$img")"
  done
fi

echo

# --- Recently finished -----------------------------------------------------
if [[ -f "$LOG_PATH" ]]; then
  echo "Recently finished:"
  recent="$(grep -E 'wrote  |✓ done' "$LOG_PATH" | grep 'wrote  ' | tail -n 5 || true)"
  if [[ -z "$recent" ]]; then
    echo "  (none in log)"
  else
    while IFS= read -r line; do
      path="$(printf '%s' "$line" | sed -E 's/.*wrote[[:space:]]+//')"
      printf '  - %s\n' "$(rel_school "$path")"
    done <<< "$recent"
  fi
fi
