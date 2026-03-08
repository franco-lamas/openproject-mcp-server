# Use a slim Python image for a small footprint
FROM python:3.11-slim AS builder

# Install build dependencies if needed
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Use application code
COPY main.py .

# Standard environment variables
ENV OPENPROJECT_HOST=http://localhost:8080
ENV OPENPROJECT_TLS_VERIFY=True
ENV LOG_LEVEL=INFO

# Expose the API port
EXPOSE 8000

# Run the server (defaults to FastAPI web server)
# To run as MCP, override command to: ["python", "main.py", "mcp"]
ENTRYPOINT ["python", "main.py"]
