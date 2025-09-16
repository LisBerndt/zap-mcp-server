# ZAP stable and versioned
FROM zaproxy/zap-stable:2.16.1

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

 # System packages (Python + curl for healthcheck + Firefox for AJAX scans)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv curl ca-certificates \
    firefox-esr \
 && rm -rf /var/lib/apt/lists/*

# Virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python dependencies (cache-friendly)
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY . /app

# Folders & permissions
RUN mkdir -p /opt/zap/session /app/logs \
 && chown -R zap:zap /opt/zap /opt/venv /app /home/zap

# Copy EntryPoint + safely remove Windows CRLF
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
 && chmod 0755 /usr/local/bin/docker-entrypoint.sh

# Back to runtime user
USER zap

# Environment
ENV ZAP_BASE=${ZAP_BASE:-http://127.0.0.1:8080} \
    ZAP_MCP_HOST=${ZAP_MCP_HOST:-0.0.0.0} \
    ZAP_MCP_PORT=${ZAP_MCP_PORT:-8082} \
    ZAP_MCP_PATH=${ZAP_MCP_PATH:-/mcp} \
    ZAP_AUTOSTART=${ZAP_AUTOSTART:-false} \
    ZAP_SESSION_NAME=${ZAP_SESSION_NAME:-zap_docker_session} \
    ZAP_SESSION_STRATEGY=${ZAP_SESSION_STRATEGY:-unique} \
    ZAP_LOG_LEVEL=${ZAP_LOG_LEVEL:-INFO} \
    ZAP_STARTUP_TIMEOUT=${ZAP_STARTUP_TIMEOUT:-120} \
    JAVA_OPTS="-Djava.awt.headless=true -Dsun.java2d.xrender=false -Dsun.java2d.noddraw=true -Dsun.java2d.opengl=false -Dsun.java2d.pmoffscreen=false -Dsun.java2d.d3d=false -Dsun.java2d.ddoffscreen=false" \
    MOZ_HEADLESS=1 \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    MOZ_DISABLE_GMP_SANDBOX=1 \
    MOZ_DISABLE_RDD_SANDBOX=1 \
    MOZ_DISABLE_GPU_SANDBOX=1 \
    MOZ_DISABLE_SOCKET_PROCESS_SANDBOX=1 \
    MOZ_DISABLE_UTILITY_SANDBOX=1

EXPOSE ${ZAP_PORT:-8080} ${ZAP_MCP_PORT:-8082}

# Healthcheck: accept 200 OR 403
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD sh -lc 'c=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${ZAP_PORT:-8080}/JSON/core/view/version || true); [ "$c" = "200" ] || [ "$c" = "403" ]'

WORKDIR /app
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-m", "zap_custom_mcp"]
