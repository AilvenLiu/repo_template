#!/bin/bash
# Common runtime helpers for agent wrapper commands.

set -euo pipefail

agent_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$script_dir/.." && pwd
}

has_poetry_project() {
  local repo_root="$1"
  if [[ ! -f "$repo_root/pyproject.toml" ]]; then
    return 1
  fi

  if ! command -v poetry >/dev/null 2>&1; then
    return 1
  fi

  if grep -qE '^\[tool\.poetry\]' "$repo_root/pyproject.toml"; then
    return 0
  fi

  if grep -q 'poetry-core' "$repo_root/pyproject.toml"; then
    return 0
  fi

  return 1
}

run_agent_python() {
  local repo_root="$1"
  shift

  if has_poetry_project "$repo_root"; then
    poetry run python "$@"
  else
    python3 "$@"
  fi
}
