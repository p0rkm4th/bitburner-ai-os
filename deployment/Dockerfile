FROM mcr.microsoft.com/playwright/python:v1.56.0-noble@sha256:a7f6cf3ae520c9d670ad956572c13747ed5abdbba5123a01526f873ed1662528

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ANONYMIZED_TELEMETRY=false \
    BROWSER_USE_CLOUD_SYNC=false DISPLAY=:99
WORKDIR /app
COPY deployment/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
 && apt-get update \
 && apt-get install -y --no-install-recommends xvfb x11vnc novnc websockify \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 --shell /usr/sbin/nologin agent
COPY app/ /app/
COPY docs/agent-game-guide.md docs/agent-tool-guide.md docs/agent-troubleshooting.md /app/docs/
COPY deployment/entrypoint.sh /app/entrypoint.sh
RUN mkdir -p /state/profile /state/checkpoints /state/logs /state/screenshots /state/saves \
 && install -d -o root -g root -m 1777 /tmp/.X11-unix \
 && chown -R agent:agent /app /state \
 && chmod +x /app/entrypoint.sh
USER agent
EXPOSE 8080 6080
CMD ["/app/entrypoint.sh"]
