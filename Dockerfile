FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends bash sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]