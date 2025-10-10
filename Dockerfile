FROM python:3.14-alpine

# Install system dependencies
RUN apk add --no-cache \
    bash \
    curl \
    git \
    unzip \
    zip \
    ca-certificates

# Install uv
RUN apk add uv

# Install opengrep
RUN curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash

# Install osv-scanner
RUN apk add osv-scanner

# Install Supercronic
RUN apk add supercronic

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies with uv
RUN uv sync --locked

# Default environment variables
ENV CONFIG_FILE=config.yaml
ENV OUTPUT_DIR=/output

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
