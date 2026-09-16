#!/usr/bin/env bash
# Kill a named OCR job (if running) and send that page to the back of the queue.
set -euo pipefail

SCHOOL_ROOT="${SCHOOL_ROOT:-$HOME/school}"
SKIP_FILE="${OCR_SKIP_FILE:-$HOME/Library/Application Support/ocr-to-md/skipped-images}"
DEFER_FILE="${OCR_DEFER_FILE:-$HOME/Library/Application Support/ocr-to-md/deferred-images}"
CHECK_SCRIPT="${OCR_CHECK_SCRIPT:-}"

if [[ -z "$CHECK_SCRIPT" ]]; then
  if [[ -f "$HOME/.cursor/skills/ocr-check/resources/ocr-check.sh" ]]; then
    CHECK_SCRIPT="$HOME/.cursor/skills/ocr-check/resources/ocr-check.sh"
  elif [[ -f "$HOME/dev/Agent_Skills/skills/ocr-check/resources/ocr-check.sh" ]]; then
    CHECK_SCRIPT="$HOME/dev/Agent_Skills/skills/ocr-check/resources/ocr-check.sh"
  fi
fi

usage() {
  echo "Usage: ocr-terminate.sh <image-name-or-queue-number>" >&2
  echo "Example: ocr-terminate.sh IMG_3389.heic" >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
QUERY="$(printf '%s' "$*")"
QUERY="${QUERY#"${QUERY%%[![:space:]]*}"}"
QUERY="${QUERY%"${QUERY##*[![:space:]]}"}"
[[ -n "$QUERY" ]] || usage

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

is_deferred() {
  local img="$1" base
  [[ -f "$DEFER_FILE" ]] || return 1
  base="$(basename "$img")"
  grep -Fxq -- "$base" "$DEFER_FILE" || grep -Fxq -- "$img" "$DEFER_FILE"
}

rel_school() {
  local path="$1"
  if [[ "$path" == "$SCHOOL_ROOT/"* ]]; then
    printf '%s\n' "${path#"$SCHOOL_ROOT"/}"
  else
    printf '%s\n' "$path"
  fi
}

kill_tree() {
  local pid="$1" kids
  kids="$(pgrep -P "$pid" 2>/dev/null || true)"
  local k
  for k in $kids; do
    kill_tree "$k"
  done
  kill "$pid" 2>/dev/null || true
}

current_image=""
current_pid=""
ps_dump="$(ps -axww -o pid=,command= 2>/dev/null || ps aux)"
ocr_line="$(printf '%s\n' "$ps_dump" | grep -E 'scripts/ocr-to-md |/ocr-to-md ' | grep -v -E 'watch-inbox|ocr-check|ocr-terminate|ocrstatus|grep' | head -1 || true)"
if [[ -n "$ocr_line" ]]; then
  current_pid="$(printf '%s\n' "$ocr_line" | awk '{ print $1 }')"
  current_image="${ocr_line##*ocr-to-md }"
  current_image="${current_image#--force }"
  current_image="${current_image#"${current_image%%[![:space:]]*}"}"
fi

candidates=()
if [[ -n "$current_image" ]]; then
  candidates+=("$current_image")
fi

ready=()
deferred=()
while IFS= read -r -d '' inbox; do
  while IFS= read -r img; do
    [[ -n "$img" ]] || continue
    is_image "$img" || continue
    is_skipped "$img" && continue
    md="${img%.*}.md"
    if [[ -f "$md" ]]; then
      continue
    fi
    if [[ -n "$current_image" && "$img" == "$current_image" ]]; then
      continue
    fi
    if is_deferred "$img"; then
      deferred+=("$img")
    else
      ready+=("$img")
    fi
    already=0
    for seen in "${candidates[@]+"${candidates[@]}"}"; do
      [[ "$seen" == "$img" ]] && already=1
    done
    if [[ $already -eq 0 ]]; then
      candidates+=("$img")
    fi
  done < <(find "$inbox" -maxdepth 2 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o -iname '*.heic' -o -iname '*.heif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.gif' -o -iname '*.bmp' \) -print 2>/dev/null | LC_ALL=C sort)
done < <(find "$SCHOOL_ROOT" -type d -name 'OCR Inbox' -print0 2>/dev/null)

ordered_deferred=()
if [[ -f "$DEFER_FILE" ]]; then
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    for img in "${deferred[@]+"${deferred[@]}"}"; do
      if [[ "$img" == "$line" || "$(basename "$img")" == "$line" ]]; then
        already=0
        for seen in "${ordered_deferred[@]+"${ordered_deferred[@]}"}"; do
          [[ "$seen" == "$img" ]] && already=1
        done
        if [[ $already -eq 0 ]]; then
          ordered_deferred+=("$img")
        fi
      fi
    done
  done < "$DEFER_FILE"
fi
for img in "${deferred[@]+"${deferred[@]}"}"; do
  already=0
  for seen in "${ordered_deferred[@]+"${ordered_deferred[@]}"}"; do
    [[ "$seen" == "$img" ]] && already=1
  done
  if [[ $already -eq 0 ]]; then
    ordered_deferred+=("$img")
  fi
done

queue=()
for img in "${ready[@]+"${ready[@]}"}"; do
  queue+=("$img")
done
for img in "${ordered_deferred[@]+"${ordered_deferred[@]}"}"; do
  queue+=("$img")
done

target=""
query_lc="$(printf '%s' "$QUERY" | tr '[:upper:]' '[:lower:]')"

if [[ "$QUERY" =~ ^[#]?[0-9]+$ ]]; then
  num="${QUERY#\#}"
  if [[ "$num" -lt 1 || "$num" -gt ${#queue[@]} ]]; then
    echo "OCR Terminate"
    echo "============="
    echo
    echo "No queue item numbered $num."
    echo
    if [[ -n "$CHECK_SCRIPT" ]]; then
      bash "$CHECK_SCRIPT"
    fi
    exit 1
  fi
  target="${queue[$((num - 1))]}"
else
  matches=()
  for img in "${candidates[@]+"${candidates[@]}"}"; do
    base="$(basename "$img")"
    stem="${base%.*}"
    rel="$(rel_school "$img")"
    img_lc="$(printf '%s' "$img" | tr '[:upper:]' '[:lower:]')"
    base_lc="$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]')"
    stem_lc="$(printf '%s' "$stem" | tr '[:upper:]' '[:lower:]')"
    rel_lc="$(printf '%s' "$rel" | tr '[:upper:]' '[:lower:]')"
    if [[ "$img_lc" == "$query_lc" || "$base_lc" == "$query_lc" || "$stem_lc" == "$query_lc" || "$rel_lc" == "$query_lc" ]]; then
      matches+=("$img")
      continue
    fi
    case "$img_lc" in *"$query_lc"*) matches+=("$img") ;; esac
  done
  # Unique matches
  uniq=()
  for img in "${matches[@]+"${matches[@]}"}"; do
    already=0
    for seen in "${uniq[@]+"${uniq[@]}"}"; do
      [[ "$seen" == "$img" ]] && already=1
    done
    if [[ $already -eq 0 ]]; then
      uniq+=("$img")
    fi
  done
  if [[ ${#uniq[@]} -eq 0 ]]; then
    echo "OCR Terminate"
    echo "============="
    echo
    printf 'No running or queued OCR matched %s\n' "$QUERY"
    echo
    if [[ -n "$CHECK_SCRIPT" ]]; then
      bash "$CHECK_SCRIPT"
    fi
    exit 1
  fi
  if [[ ${#uniq[@]} -gt 1 ]]; then
    echo "OCR Terminate"
    echo "============="
    echo
    printf 'Several pages matched %s. Name one of these exactly:\n' "$QUERY"
    for img in "${uniq[@]}"; do
      printf '  - %s\n' "$(rel_school "$img")"
    done
    exit 1
  fi
  target="${uniq[0]}"
fi

mkdir -p "$(dirname "$DEFER_FILE")"
touch "$DEFER_FILE"
tmp="$(mktemp "${TMPDIR:-/tmp}/ocr-defer.XXXXXX")"
base="$(basename "$target")"
grep -Fxv -- "$target" "$DEFER_FILE" | grep -Fxv -- "$base" > "$tmp" || true
printf '%s\n' "$target" >> "$tmp"
mv "$tmp" "$DEFER_FILE"

killed="no"
if [[ -n "$current_image" && "$target" == "$current_image" && -n "$current_pid" ]]; then
  kill_tree "$current_pid"
  sleep 0.4
  if kill -0 "$current_pid" 2>/dev/null; then
    kill -9 "$current_pid" 2>/dev/null || true
  fi
  killed="yes"
fi

echo "OCR Terminate"
echo "============="
echo
printf 'Target:  %s\n' "$(rel_school "$target")"
if [[ "$killed" == "yes" ]]; then
  echo "Action:  killed the live OCR process and moved this page to the back of the queue"
else
  echo "Action:  not running; moved this page to the back of the queue"
fi
echo

if [[ -n "$CHECK_SCRIPT" ]]; then
  bash "$CHECK_SCRIPT"
fi
