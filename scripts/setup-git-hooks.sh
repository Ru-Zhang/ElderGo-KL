#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$ROOT/.githooks/commit-msg"
git -C "$ROOT" config core.hooksPath .githooks
echo "Git hooks enabled: $ROOT/.githooks (strips Cursor co-author trailers)"
