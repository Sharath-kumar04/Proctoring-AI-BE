FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create venv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    default-mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy only necessary files
COPY ./scripts ./scripts/
COPY ./utils ./utils/
COPY ./models ./models/
COPY ./config ./config/
COPY ./detection ./detection/
COPY ./routers ./routers/
COPY ./schemas ./schemas/
COPY ./services ./services/
COPY ./main.py ./
COPY ./start.sh ./

RUN chmod +x start.sh scripts/wait-for-db.sh

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/ || exit 1

RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["./start.sh"]