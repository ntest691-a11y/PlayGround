#!/usr/bin/env bash
# Serve the built static directory in the foreground on PORT (default 3000).
# Writes the deployment-output.json pointer for the controller.
set -euo pipefail
/usr/bin/time -p test -f "$(dirname "$0")/site/index.html"
/usr/bin/time -p mkdir -p /home/runner/work/_temp/omgithub-web
/usr/bin/time -p printf '%s' '{"project":"/home/runner/work/PlayGround/PlayGround","directory":"/home/runner/work/PlayGround/PlayGround/site"}' > /home/runner/work/_temp/omgithub-web/deployment-output.json
/usr/bin/time -p cat /home/runner/work/_temp/omgithub-web/deployment-output.json
/usr/bin/time -p bash -c 'cd "/home/runner/work/PlayGround/PlayGround/site" && pwd'
cd "/home/runner/work/PlayGround/PlayGround/site"
/usr/bin/time -p python3 --version
PORT="${PORT:-3000}"
export PORT
/usr/bin/time -p printf 'Serving %s on port %s\n' "$PWD" "$PORT"
exec /usr/bin/time -p python3 -m http.server "$PORT" --bind 0.0.0.0
