#!/usr/bin/env bash
# Capture desktop + mobile screenshots of CAPTURE_URL into CAPTURE_DIR.
# Leaves the app server running; output stays outside the source tree.
# Exit 75 = temporary navigation/browser infra failure, exit 1 = script/rendering defect.
set -euo pipefail
/usr/bin/time -p test -n "${CAPTURE_URL:?Set CAPTURE_URL to the exact preview URL.}"
/usr/bin/time -p test -n "${CAPTURE_DIR:?Set CAPTURE_DIR to the screenshot output directory.}"
/usr/bin/time -p test -n "${RUNTIME_DIR:?Set RUNTIME_DIR to the runtime scripts directory.}"
/usr/bin/time -p mkdir -p "$CAPTURE_DIR"
/usr/bin/time -p node "${RUNTIME_DIR}/scripts/default-capture.mjs"
/usr/bin/time -p test -f "$CAPTURE_DIR/final-desktop.png"
/usr/bin/time -p test -f "$CAPTURE_DIR/final-mobile.png"
/usr/bin/time -p ls -lh "$CAPTURE_DIR/final-desktop.png" "$CAPTURE_DIR/final-mobile.png"
