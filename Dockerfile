# Build
FROM python:3.11 AS builder
WORKDIR /app

# build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime
FROM python:3.11-alpine
WORKDIR /app

# runtime dependencies
RUN apk add --no-cache \
    libgcc \
    libstdc++

COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000

CMD ["python", "app.py"]
