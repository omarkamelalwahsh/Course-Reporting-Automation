# 1. Base Image - Stable & Reliable
FROM python:3.11-slim-bookworm

# 2. Environment Meta
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# 3. System Dependencies - Layer cached unless this list changes
# This set of libraries is essential for Chromium to run on Debian 12.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    libgomp1 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libxshmfence1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxkbcommon0 \
    libxfixes3 \
    libxrender1 \
    libxext6 \
    libgtk-3-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 4. Python Dependencies - Layer cached unless requirements.api.txt changes
COPY requirements.api.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.api.txt

# 5. Playwright Browser - Layer cached unless pip/requirements change
# Installing the browser early so code changes don't trigger re-download
RUN python -m playwright install chromium

# 6. Project Code - Only this layer re-runs when you change your code
COPY . .

# 7. Final Prep
RUN mkdir -p /app/outputs
EXPOSE 8001

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
