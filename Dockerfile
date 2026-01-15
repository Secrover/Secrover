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
RUN apk add --no-cache uv

# Install opengrep
RUN curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh -o /tmp/install.sh && \
    chmod +x /tmp/install.sh && \
    bash /tmp/install.sh
ENV PATH="/root/.opengrep/cli/latest:$PATH"

# Install osv-scanner
RUN apk add --no-cache osv-scanner

# Install Supercronic
RUN apk add --no-cache supercronic

# Install rclone
RUN apk add --no-cache rclone

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies with uv
RUN uv sync --locked

# Download ip2location db
RUN mkdir -p data/IP2Location && \
    curl -L -o /tmp/ip2loc.zip "https://download.ip2location.com/lite/IP2LOCATION-LITE-DB1.BIN.ZIP" && \
    unzip /tmp/ip2loc.zip -d data/IP2Location && \
    rm -f /tmp/ip2loc.zip

ENV IP2LOCATION_DB_PATH="data/IP2Location/IP2LOCATION-LITE-DB1.BIN"

# Default environment variables
ENV CONFIG_FILE="/config.yaml"
ENV OUTPUT_DIR="/output/"
ENV REPOS_DIR="repos/"
ENV EXPORT_ENABLED="false"
ENV RCLONE_REMOTES=""
ENV RCLONE_PATH="/secrover-reports/"

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
