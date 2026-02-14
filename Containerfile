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

# Use Hummingbird Python image (Red Hat UBI-based with Python pre-installed)
FROM quay.io/hummingbird/python:latest

# Labels for container metadata
LABEL name="mcp-cloudflare-crunchtools" \
      version="0.1.0" \
      summary="Secure MCP server for Cloudflare DNS, Transform Rules, and Page Rules" \
      description="A security-focused MCP server for Cloudflare built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-cloudflare" \
      io.k8s.display-name="MCP Cloudflare CrunchTools" \
      io.openshift.tags="mcp,cloudflare,dns"

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system --no-cache .

# Verify installation
RUN python -c "from mcp_cloudflare_crunchtools import main; print('Installation verified')"

# MCP servers run via stdio, so we need interactive mode
# The entrypoint runs the MCP server
ENTRYPOINT ["python", "-m", "mcp_cloudflare_crunchtools"]

# No CMD needed - the server reads from stdin and writes to stdout
