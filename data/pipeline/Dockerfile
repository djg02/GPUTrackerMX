FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY pipeline/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m camoufox fetch

RUN mkdir -p /app/logs

COPY . .

CMD ["bash", "-c", "while true; do bash pipeline/run_pipeline.sh >> /app/logs/pipeline_$(date +%Y-%m-%d_%H-%M-%S).log 2>&1; sleep 28800; done"]