# MCP Cloudflare CrunchTools Container
# Built on Hummingbird Python image (Red Hat UBI-based) for enterprise security
#
# Build:
#   podman build -t quay.io/crunchtools/mcp-cloudflare .
#
# Run:
#   podman run -e CLOUDFLARE_API_TOKEN=your_token quay.io/crunchtools/mcp-cloudflare
#
# With Claude Code:
#   claude mcp add mcp-cloudflare \
#     --env CLOUDFLARE_API_TOKEN=your_token \
#     -- podman run -i --rm -e CLOUDFLARE_API_TOKEN quay.io/crunchtools/mcp-cloudflare

# Stage 1: Lock (turn uv.lock into the exact dependency set to install)
FROM quay.io/hummingbird/python:3.14-builder AS lock
USER 0
RUN pip install --no-cache-dir uv==0.13.7
WORKDIR /lock
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project \
      --format requirements-txt -o /requirements.txt

# Stage 2: Builder (has a shell, dnf and build tools)
FROM quay.io/hummingbird/python:3.14-builder AS builder
USER 0
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
# Dependencies come from uv.lock, not from a fresh resolve. `pip install .`
# read only pyproject.toml, whose floors carry no upper bound, so the image
# shipped whatever had been released that morning -- a dependency set no test
# had ever run against (RT#1564). --no-deps stops pip re-resolving what the
# lock already decided.
COPY --from=lock /requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-deps -r /tmp/requirements.txt
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

# Stage 3: Runtime (distroless -- no shell, no package manager)
FROM quay.io/hummingbird/python:3.14

# Labels for container metadata
LABEL name="mcp-cloudflare-crunchtools" \
      version="0.9.1" \
      summary="Secure MCP server for Cloudflare DNS, Transform Rules, and Page Rules" \
      description="A security-focused MCP server for Cloudflare built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-cloudflare" \
      io.k8s.display-name="MCP Cloudflare CrunchTools" \
      io.openshift.tags="mcp,cloudflare,dns" \
      org.opencontainers.image.source="https://github.com/crunchtools/mcp-cloudflare" \
      org.opencontainers.image.description="Secure MCP server for Cloudflare DNS, Transform Rules, and Page Rules" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /app

COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Verify the install. Exec form: this stage has no /bin/sh for RUN's shell form.
RUN ["python3", "-c", "from mcp_cloudflare_crunchtools import main; print('Installation verified')"]

# Default: stdio transport (use -i with podman run)
# HTTP:    --transport streamable-http (use -d -p 8000:8000 with podman run)
EXPOSE 8000
ENTRYPOINT ["python", "-m", "mcp_cloudflare_crunchtools"]
