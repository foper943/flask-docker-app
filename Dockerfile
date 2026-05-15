FROM python:3.12-slim

WORKDIR /app

# curl нужен для HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — слой кэшируется пока requirements.txt не изменится
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения — обновляется чаще, идёт последним
COPY . .

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
