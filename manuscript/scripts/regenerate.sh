#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIRECTORY=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec bash "$SCRIPT_DIRECTORY/in_container.sh" python "$SCRIPT_DIRECTORY/regenerate.py"
