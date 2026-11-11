#!/usr/bin/env bash
# Publish a built site to the gh-pages branch, which GitHub Pages serves.
#
#   scripts/publish-pages.sh results/site .                  the site itself (keeps pr-preview/)
#   scripts/publish-pages.sh results/site pr-preview/pr-12   a preview of pull request 12
#   scripts/publish-pages.sh - pr-preview/pr-12              remove that preview
#
# Run from a clone that can push to origin (in GitHub Actions: after actions/checkout).
# Several workflows publish; a push that loses a race is retried on the new tip.
set -euo pipefail

src=$1
dest=$2
[[ $dest == . || $dest =~ ^pr-preview/pr-[0-9]+$ ]] || { echo "unexpected destination: $dest" >&2; exit 2; }
if [[ $src != - ]]; then
  [[ -d $src ]] || { echo "no site folder at $src" >&2; exit 2; }
  src=$(realpath "$src")
fi
work=$(mktemp -d)
trap 'git worktree remove --force "$work" >/dev/null 2>&1 || true' EXIT

# One attempt. `set -e` does not apply inside a function called from `if`, so every step
# that can fail ends the attempt explicitly.
publish() {
  git worktree remove --force "$work" >/dev/null 2>&1 || true
  rm -rf "$work"
  if git fetch --quiet --depth 1 origin gh-pages 2>/dev/null; then
    git worktree add --quiet --detach "$work" FETCH_HEAD || return 1
  else  # first publish: start the branch empty
    git worktree add --quiet --detach "$work" || return 1
    git -C "$work" checkout --quiet --orphan gh-pages || return 1
    git -C "$work" rm -rfq --ignore-unmatch . || return 1
  fi
  cd "$work" || return 1
  if [[ $dest == . ]]; then
    find . -mindepth 1 -maxdepth 1 ! -name .git ! -name pr-preview -exec rm -rf {} + || return 1
    cp -R "$src"/. . || return 1
  else
    rm -rf "$dest" || return 1
    if [[ $src != - ]]; then
      mkdir -p "$dest" && cp -R "$src"/. "$dest" || return 1
    fi
  fi
  touch .nojekyll || return 1  # serve the files as they are, without Jekyll
  git add -A || return 1
  if git diff --cached --quiet; then
    echo "gh-pages: $dest is already up to date"
    return 0
  fi
  git -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit --quiet -m "Publish $dest from ${GITHUB_SHA:-a local build}" || return 1
  git push --quiet origin HEAD:refs/heads/gh-pages || return 1
  echo "gh-pages: published $dest"
}

here=$PWD
for attempt in 1 2 3 4 5; do
  cd "$here"
  if publish; then
    exit 0
  fi
  echo "gh-pages: attempt $attempt failed; retrying on the latest gh-pages" >&2
  sleep $((attempt * 5))
done
exit 1
