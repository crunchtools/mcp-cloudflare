# MCP Cloudflare CrunchTools Container
# Built on Red Hat Universal Base Image for enterprise security
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

# Use Red Hat Universal Base Image with Python 3.12
FROM registry.access.redhat.com/ubi9/python-312:latest

# Labels for container metadata
LABEL name="mcp-cloudflare-crunchtools" \
      version="0.1.0" \
      summary="Secure MCP server for Cloudflare DNS, Transform Rules, and Page Rules" \
      description="A security-focused MCP server for Cloudflare built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-cloudflare" \
      io.k8s.display-name="MCP Cloudflare CrunchTools" \
      io.openshift.tags="mcp,cloudflare,dns"

# Switch to root to install system packages if needed
USER 0

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Switch back to default user (1001)
USER 1001

# Set working directory
WORKDIR /opt/app-root/src

# Copy project files
COPY --chown=1001:0 pyproject.toml README.md ./
COPY --chown=1001:0 src/ ./src/

# Install dependencies using uv
RUN uv pip install --system --no-cache .

# Verify installation
RUN python -c "from mcp_cloudflare_crunchtools import main; print('Installation verified')"

# MCP servers run via stdio, so we need interactive mode
# The entrypoint runs the MCP server
ENTRYPOINT ["python", "-m", "mcp_cloudflare_crunchtools"]

# No CMD needed - the server reads from stdin and writes to stdout
