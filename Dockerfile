FROM node:22-slim AS  dashboard_builder

WORKDIR /dashboard
COPY  app/dashboard/package.json app/dashboard/package-lock.json ./
RUN npm ci

COPY app/dashboard/ ./
RUN npm run build


FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends bash sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/ ./app
COPY main.py .
COPY requirements.txt .

RUN rm -rf ./app/dashboard

COPY --from=dashboard_builder /dashboard/dist ./app/dashboard_build

RUN mkdir -p ./app/data
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]