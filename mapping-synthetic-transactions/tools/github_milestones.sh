#!/usr/bin/env bash
# Medianville on GitHub: milestones, the merged PRs filed under them, annotated tags at
# the commits where code-bearing milestones ended, and a release for each tag.
#
#   tools/github_milestones.sh                 dry run (the default): read GitHub, print every change
#   tools/github_milestones.sh --apply         make the changes
#   tools/github_milestones.sh --offline       dry run without reading GitHub (assumes nothing exists yet)
#   tools/github_milestones.sh --only milestones|prs|tags|releases   one step (dry run or --apply)
#
# Run it from Jason's Mac, from anywhere in the repo, after the pull request that adds story/ and
# archive/ has merged into development and been promoted to main: the milestone descriptions and
# release notes link to story/ on main. Needs gh (logged in, with repo scope), git and zip.
#
# Running it twice changes nothing the second time: milestones are matched by title and only
# patched where they differ, PRs already filed are skipped, tags that exist are left alone (and an
# existing tag on a different commit stops the script), and a release that exists only gets its
# missing assets uploaded; its notes keep the date they were first published.
#
# The release notes are tools/release-notes/<tag>.md; {{PUBLISHED}} becomes today's date.
# The repo's other milestones belong to other projects, so every title starts "Medianville · ".
set -eo pipefail   # no -u: bash 3.2 (macOS) treats "${empty[@]}" as unbound

REPO="jas0nmjames/playground"
BRANCH="main"   # where the story links point
STORY="https://github.com/$REPO/tree/$BRANCH/mapping-synthetic-transactions/story"

APPLY=0; OFFLINE=0; ONLY="all"
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --dry-run) APPLY=0 ;;
    --offline) OFFLINE=1 ;;
    --only) ONLY="$2"; shift ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
[ "$APPLY" = 1 ] && [ "$OFFLINE" = 1 ] && { echo "--offline is for dry runs only" >&2; exit 2; }

cd "$(git rev-parse --show-toplevel)"
NOTES_DIR="mapping-synthetic-transactions/tools/release-notes"
TODAY="$(date +%F)"
MODE=$([ "$APPLY" = 1 ] && echo "APPLY" || echo "DRY RUN")
echo "== Medianville on GitHub ($MODE$([ "$OFFLINE" = 1 ] && echo ", offline"))"

run() {  # print a command; run it only with --apply
  printf '  $'; printf ' %q' "$@"; printf '\n'
  if [ "$APPLY" = 1 ]; then "$@"; fi
}
step() { [ "$ONLY" = all ] || [ "$ONLY" = "$1" ]; }

# ─── the milestones ──────────────────────────────────────────────────────────
# key | title | state | due date (end date; empty = none) | story folder | two lines
MILESTONES=(
  "M0|Medianville · M0 The idea|closed|2026-11-16|00-the-idea|Before 2026-11-16: transactions as jobs to be done, a synthetic city instead of a real one, the systems lens and the four clocks.
No pull requests: the white paper and the city design came into the repo with M1, in #54."
  "M1|Medianville · M1 One day|closed|2026-11-17|01-one-day|Nov 16–17: the generator prompt, the simulator, the 201,753-record day (halvern_2027-03-03.zip), the 500 hand-written records and the first viewer.
Release: medianville-m1-one-day."
  "M2|Medianville · M2 Miniature and Map|closed|2026-11-17|02-miniature-and-map|Nov 17: three visual directions prototyped in the Claude app, Tabletop chosen, then v3: two views of one city. No viewer v2 shipped.
Release: medianville-m2-miniature-and-map."
  "M3|Medianville · M3 Grounding in evidence|closed|2026-11-19|03-grounding-in-evidence|Nov 17–19: the human-evidence research (69 sources), the data update plan, the evidence targets and the downloaded datasets; data plan phases 0–2.
Phase 0 and the start of 2 were commit e077162, pushed straight to development; the evidence files came in #86 on Nov 22. No release."
  "M4|Medianville · M4 The refined city|closed|2026-11-20|04-the-refined-city|Nov 18–20: the systems lens, mapped blocks, the photographic miniature, sound, the data explorer, the repo reorganized, the intro and About, and the rename to Medianville.
Release: medianville-m4-the-refined-city."
  "M5|Medianville · M5 More time|closed|2026-11-21|05-more-time|Nov 20–21: v2's simulator changes (phase 3), the typed-day year, the March 2027 month (phase 4), close reading and publishing (phase 5), and the lens's district tier (#82, \"phase 6\").
Release: medianville-m5-more-time; the month is medianville-v2-month-2027-03."
  "M6|Medianville · M6 Refinements|open||06-refinements|From Nov 21, ongoing: polish, rendering fixes, the day control, Sound on the city, the explorer header, and the story and archive.
Pushed straight to development on Nov 23, so not filed here: 63c8731, 384a19f, 46851e2, 9ccbd7a, a49d14c, d08935d, 175551d, 8275a2e."
  "M7|Medianville · M7 Open to agents|open||07-open-to-agents|From Nov 24, ongoing: the site made readable by agents and LLMs. First pass: llms.txt, the agents/ pages, a data dictionary, licenses and metadata, and Copy for AI.
Still to come: Parquet and a Hugging Face dataset, a local MCP server, Open in links and an eval set."
  "NEXT|Medianville · Next: mining for projects|open||next-mining-for-projects|Not started. The project's actual goal: rank the frictions, recheck the project leads, and make the field visits.
Its tasks are issues filed here."
)

# ─── the merged PRs, by milestone ────────────────────────────────────────────
# Left unfiled on purpose: development → main promotions (#55 #58 #59 #70 #73 #76 #84 #87 #88 #89),
# Dependabot, and #74 (Small as Voyager). #60 is M4 (it's the lens), not M3; #82 is M5 (it shipped as
# a v2 phase), though it's mostly lens work. Add the PR for each new piece of Medianville work here.
PRS=(
  "M1|54"
  "M2|57"
  "M3|61 65 86"
  "M4|60 63 64 66 67 68 69 72 77"
  "M5|71 78 80 81 82"
  "M6|83 85 90"
  "M7|134"
)

# ─── tags and releases ───────────────────────────────────────────────────────
# tag | commit | release title | key
TAGS=(
  "medianville-m1-one-day|2379e72|Medianville · M1 One day|M1"
  "medianville-m2-miniature-and-map|9e0865e|Medianville · M2 Miniature and Map|M2"
  "medianville-m4-the-refined-city|7013a0f|Medianville · M4 The refined city|M4"
  "medianville-m5-more-time|23265ff|Medianville · M5 More time|M5"
)
# Kept as it is: medianville-v2-month-2027-03 at 1451a1d (#78), the release that carries the month.

field() { echo "$1" | head -1 | cut -d'|' -f"$2"; }   # entries' later lines are description text

# Existing milestones, as parallel arrays (macOS ships bash 3.2, which has no associative arrays).
EX_NUM=(); EX_TITLE=(); EX_STATE=(); EX_DUE=()
if [ "$OFFLINE" = 0 ]; then
  while IFS=$'\t' read -r num title state due; do
    [ -n "$num" ] || continue
    EX_NUM+=("$num"); EX_TITLE+=("$title"); EX_STATE+=("$state"); EX_DUE+=("${due:0:10}")
  done < <(gh api --paginate "repos/$REPO/milestones?state=all&per_page=100" \
             --jq '.[] | select(.title | startswith("Medianville · ")) | [.number, .title, .state, (.due_on // "")] | @tsv')
fi
existing() {  # index of the existing milestone with this title, or -1
  local i=0
  while [ "$i" -lt "${#EX_TITLE[@]}" ]; do
    [ "${EX_TITLE[$i]}" = "$1" ] && { echo "$i"; return; }
    i=$((i + 1))
  done
  echo -1
}

# Each milestone key's number: KEYNUM_M0, KEYNUM_M1 … (or "(new: …)" until it's created)
for m in "${MILESTONES[@]}"; do
  key=$(field "$m" 1); title=$(field "$m" 2); i=$(existing "$title")
  if [ "$i" -ge 0 ]; then printf -v "KEYNUM_$key" '%s' "${EX_NUM[$i]}"; else printf -v "KEYNUM_$key" '%s' "(new: $title)"; fi
done
key_num() { local v="KEYNUM_$1"; echo "${!v}"; }

# ─── 1. milestones ───────────────────────────────────────────────────────────

if step milestones; then
  echo; echo "-- 1. Milestones"
  for m in "${MILESTONES[@]}"; do
    key=$(field "$m" 1); title=$(field "$m" 2); state=$(field "$m" 3); due=$(field "$m" 4); folder=$(field "$m" 5)
    lines=$(echo "$m" | cut -d'|' -f6-)
    desc="$lines
Story: $STORY/$folder"
    args=(-f "title=$title" -f "state=$state" -f "description=$desc")
    [ -n "$due" ] && args+=(-f "due_on=${due}T12:00:00Z")
    i=$(existing "$title"); num=""; have_state=""; have_due=""; have_desc=""
    if [ "$i" -ge 0 ]; then
      num=${EX_NUM[$i]}; have_state=${EX_STATE[$i]}; have_due=${EX_DUE[$i]}
      have_desc=$(gh api "repos/$REPO/milestones/$num" --jq .description)
    fi
    if [ -z "$num" ]; then
      echo "create  $title  [$state${due:+, due $due}]"
      echo "$desc" | sed 's/^/          | /'
      if [ "$APPLY" = 1 ]; then
        printf -v "KEYNUM_$key" '%s' "$(gh api -X POST "repos/$REPO/milestones" "${args[@]}" --jq .number)"
        echo "          → milestone $(key_num "$key")"
      else
        printf '  $ gh api -X POST repos/%s/milestones -f title=%q -f state=%s%s -f description=…\n' "$REPO" "$title" "$state" "${due:+ -f due_on=${due}T12:00:00Z}"
      fi
    elif [ "$have_state" != "$state" ] || [ "$have_due" != "$due" ] || [ "$have_desc" != "$desc" ]; then
      echo "update  #$num $title  [$have_state → $state; due ${have_due:-none} → ${due:-none}; description $([ "$have_desc" = "$desc" ] && echo same || echo changes)]"
      upd=(-f "state=$state" -f "description=$desc")
      if [ -n "$due" ]; then upd+=(-f "due_on=${due}T12:00:00Z"); elif [ -n "$have_due" ]; then upd+=(-F "due_on=null"); fi
      run gh api -X PATCH "repos/$REPO/milestones/$num" "${upd[@]}" --silent
    else
      echo "ok      #$num $title"
    fi
  done
fi

# ─── 2. file the merged PRs ──────────────────────────────────────────────────
if step prs; then
  echo; echo "-- 2. Pull requests → milestones"
  for row in "${PRS[@]}"; do
    key=${row%%|*}; nums=${row#*|}; target=$(key_num "$key")
    for n in $nums; do
      if [ "$OFFLINE" = 0 ]; then
        cur=$(gh api "repos/$REPO/issues/$n" --jq '[(.milestone.number // "" | tostring), (.pull_request.merged_at // ""), .title] | join("|")')
        IFS='|' read -r cur_ms merged ptitle <<<"$cur"
      else
        cur_ms=""; merged="(not checked)"; ptitle=""
      fi
      label="#$n → $key ${ptitle:+($ptitle)}"
      [ -z "$merged" ] && { echo "skip    $label: not merged"; continue; }
      if [ "$cur_ms" = "$target" ]; then
        echo "ok      $label"
      else
        echo "file    $label${cur_ms:+ (was milestone $cur_ms)}"
        if [[ "$target" == "(new"* ]]; then
          printf '  $ gh api -X PATCH repos/%s/issues/%s -F milestone=<%s>\n' "$REPO" "$n" "$key"
        else
          run gh api -X PATCH "repos/$REPO/issues/$n" -F "milestone=$target" --silent
        fi
      fi
    done
  done
fi

# ─── 3. annotated tags ───────────────────────────────────────────────────────
if step tags; then
  echo; echo "-- 3. Tags"
  [ "$OFFLINE" = 0 ] && git fetch --quiet --tags origin
  for t in "${TAGS[@]}"; do
    tag=$(field "$t" 1); sha=$(field "$t" 2); title=$(field "$t" 3)
    full=$(git rev-parse --verify "$sha^{commit}")
    if have=$(git rev-parse -q --verify "refs/tags/$tag^{commit}"); then
      [ "$have" = "$full" ] || { echo "STOP    $tag exists at ${have:0:7}, not $sha: not moving it" >&2; exit 1; }
      if [ "$OFFLINE" = 0 ] && ! git ls-remote --exit-code --tags origin "refs/tags/$tag" >/dev/null; then
        echo "push    $tag (exists here, not on GitHub)"; run git push origin "refs/tags/$tag"
      else
        echo "ok      $tag at $sha"
      fi
    else
      echo "create  $tag at $sha ($(git log -1 --format='%ad %s' --date=short "$sha"))"
      run git tag -a "$tag" "$sha" -m "$title" -m "Medianville milestone snapshot at the commit where it ended. Story: $STORY"
      run git push origin "refs/tags/$tag"
    fi
  done
fi

# ─── 4. releases ─────────────────────────────────────────────────────────────
if step releases; then
  echo; echo "-- 4. Releases"
  TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
  for t in "${TAGS[@]}"; do
    tag=$(field "$t" 1); sha=$(field "$t" 2); title=$(field "$t" 3)
    notes_src="$NOTES_DIR/$tag.md"; [ -f "$notes_src" ] || { echo "missing $notes_src" >&2; exit 1; }
    slug=${tag#medianville-}
    zip="$TMP/mapping-synthetic-transactions-$slug.zip"
    assets=("$zip")
    [ "$tag" = medianville-m1-one-day ] && assets+=("$TMP/halvern_2027-03-03.zip")
    build_assets() {
      git archive --format=zip -o "$zip" "$sha" mapping-synthetic-transactions
      [ "$tag" = medianville-m1-one-day ] && git show "$sha:mapping-synthetic-transactions/data/halvern_2027-03-03.zip" > "$TMP/halvern_2027-03-03.zip"
      return 0
    }
    have_assets=""
    [ "$OFFLINE" = 0 ] && have_assets=$(gh release view "$tag" --repo "$REPO" --json assets --jq '.assets[].name' 2>/dev/null || echo "__none__")
    [ "$OFFLINE" = 1 ] && have_assets="__none__"
    if [ "$have_assets" = "__none__" ]; then
      size=$(git archive --format=zip "$sha" mapping-synthetic-transactions | wc -c | awk '{printf "%.1f MB", $1/1048576}')
      echo "create  $title  ($tag; assets: $(basename "$zip") $size$([ ${#assets[@]} -gt 1 ] && echo ", halvern_2027-03-03.zip"))"
      sed "s/{{PUBLISHED}}/$TODAY/" "$notes_src" > "$TMP/$tag.md"
      echo "          notes: $notes_src (first line: $(head -1 "$TMP/$tag.md" | cut -c1-90)…)"
      [ "$APPLY" = 1 ] && build_assets
      run gh release create "$tag" --repo "$REPO" --verify-tag --latest=false --title "$title" --notes-file "$TMP/$tag.md" "${assets[@]}"
    else
      missing=()
      for a in "${assets[@]}"; do grep -qx "$(basename "$a")" <<<"$have_assets" || missing+=("$a"); done
      if [ ${#missing[@]} -eq 0 ]; then
        echo "ok      $title"
      else
        echo "upload  $title: $(for a in "${missing[@]}"; do basename "$a"; done | tr '\n' ' ')"
        [ "$APPLY" = 1 ] && build_assets
        run gh release upload "$tag" --repo "$REPO" "${missing[@]}"
      fi
    fi
  done
fi

# ─── summary ────────────────────────────────────────────────────────────────
echo; echo "-- PR mapping"
for row in "${PRS[@]}"; do echo "  ${row%%|*}: $(echo "${row#*|}" | sed 's/\([0-9][0-9]*\)/#\1/g')"; done
echo "  unfiled: #55 #58 #59 #70 #73 #76 #84 #87 #88 #89 (promotions), Dependabot, #74 (Small as Voyager)"
[ "$APPLY" = 1 ] || echo; [ "$APPLY" = 1 ] || echo "Dry run: nothing was changed. Run again with --apply."
