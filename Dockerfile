FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    zip \
    gnupg \
    libzip-dev \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libicu-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    zlib1g-dev \
    libpq-dev \
    ca-certificates

# Ensure pip is installed/upgraded
RUN python -m ensurepip --upgrade && \
    pip install --upgrade pip

# Install pip-audit globally
RUN pip install pip-audit

# Install PHP and Composer
RUN apt-get install -y php-cli
RUN curl -sS https://getcomposer.org/installer | php && \
    mv composer.phar /usr/local/bin/composer

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies with uv
RUN uv sync --locked

# Default env vars
ENV CONFIG_FILE=config.yaml
ENV OUTPUT_DIR=/output

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]