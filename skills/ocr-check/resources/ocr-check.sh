#!/usr/bin/env bash
# Show the live OCR page and the inbox queue in processing order.
set -euo pipefail

SCHOOL_ROOT="${SCHOOL_ROOT:-$HOME/school}"
SKIP_FILE="${OCR_SKIP_FILE:-$HOME/Library/Application Support/ocr-to-md/skipped-images}"
DEFER_FILE="${OCR_DEFER_FILE:-$HOME/Library/Application Support/ocr-to-md/deferred-images}"

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

current_image=""
ps_dump="$(ps -axww -o pid=,command= 2>/dev/null || ps aux)"
ocr_line="$(printf '%s\n' "$ps_dump" | grep -E 'scripts/ocr-to-md |/ocr-to-md ' | grep -v -E 'watch-inbox|ocr-check|ocr-terminate|ocrstatus|grep' | head -1 || true)"
glm_line="$(printf '%s\n' "$ps_dump" | grep -E 'glm_ocr.py' | grep -v grep | head -1 || true)"

if [[ -n "$ocr_line" ]]; then
  current_image="${ocr_line##*ocr-to-md }"
  current_image="${current_image#--force }"
  current_image="${current_image#"${current_image%%[![:space:]]*}"}"
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

echo "OCR Check"
echo "========="
echo

echo "Now processing:"
if [[ -n "$current_image" ]]; then
  printf '  %s\n' "$(rel_school "$current_image")"
  printf '  file: %s\n' "$(basename "$current_image")"
  if [[ -n "$glm_line" ]]; then
    echo "  engine: glm-ocr active"
  else
    echo "  engine: ocr-to-md running (glm-ocr not visible yet)"
  fi
else
  echo "  idle (no page in progress)"
fi

echo
n=0
printf 'Queue order (%s waiting):\n' "$(( ${#ready[@]} + ${#ordered_deferred[@]} ))"
if [[ ${#ready[@]} -eq 0 && ${#ordered_deferred[@]} -eq 0 ]]; then
  echo "  (empty)"
else
  for img in "${ready[@]+"${ready[@]}"}"; do
    n=$((n + 1))
    printf '  %d. %s\n' "$n" "$(rel_school "$img")"
  done
  for img in "${ordered_deferred[@]+"${ordered_deferred[@]}"}"; do
    n=$((n + 1))
    printf '  %d. %s  [back of queue]\n' "$n" "$(rel_school "$img")"
  done
fi
