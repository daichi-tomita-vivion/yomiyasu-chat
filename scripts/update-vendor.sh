#!/usr/bin/env bash
# nanaism/yomiyasu の yomiyasu_lint.py を指定タグから取り直す。
# 使い方: scripts/update-vendor.sh v1.0.7
set -euo pipefail
TAG="${1:?usage: $0 <tag e.g. v1.0.6>}"
DIR="$(cd "$(dirname "$0")" && pwd)/vendor"
BASE="https://raw.githubusercontent.com/nanaism/yomiyasu/${TAG}"
curl -fsSL "${BASE}/scripts/yomiyasu_lint.py" -o "${DIR}/yomiyasu_lint.py"
curl -fsSL "${BASE}/LICENSE" -o "${DIR}/LICENSE.yomiyasu"
echo "${TAG}" > "${DIR}/VERSION"
python3 -c "import ast,sys; ast.parse(open('${DIR}/yomiyasu_lint.py').read())"
echo "updated to ${TAG}"
