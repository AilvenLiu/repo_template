#!/bin/bash
# Thin Claude Code adapter. Canonical hook logic lives under .agents/hooks/.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$REPO_ROOT/.agents/hooks/pre_tool_use.sh"
