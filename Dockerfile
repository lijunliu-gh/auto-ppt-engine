FROM python:3.12-slim AS base

# Install Node.js 20 (needed for JS renderer)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
COPY package.json ./
RUN npm install --omit=dev

# Copy application code
COPY . .

# Default output directory
RUN mkdir -p /app/output

# In Docker, bind to all interfaces and use port 5000
ENV HOST=0.0.0.0
ENV PORT=5000

# Expose HTTP skill server port
EXPOSE 5000

# Default entrypoint — runs the HTTP skill server
# Override with: docker run ... python mcp_server.py (for stdio MCP)
#            or: docker run ... python py-generate-from-prompt.py --mock --prompt "..."
CMD ["python", "py-skill-server.py"]
