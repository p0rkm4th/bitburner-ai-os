#!/bin/sh
set -eu
rm -f /state/profile/SingletonLock /state/profile/SingletonCookie /state/profile/SingletonSocket
Xvfb :99 -screen 0 "${SCREEN_SIZE:-1440x900x24}" -nolisten tcp &
if [ "${VNC_INTERACTIVE:-0}" = "1" ]; then
  x11vnc -display :99 -forever -shared -localhost -nopw -quiet &
else
  x11vnc -display :99 -forever -shared -localhost -nopw -viewonly -quiet &
fi
websockify --web=/usr/share/novnc/ 6080 localhost:5900 &
exec uvicorn server:app --host 0.0.0.0 --port 8080
