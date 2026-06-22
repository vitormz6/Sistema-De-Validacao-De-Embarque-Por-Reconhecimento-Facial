FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app/apps/edge-api

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/edge-api/ ./

RUN pip install --upgrade pip \
    && pip install -e .

RUN chmod +x entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["sh", "entrypoint.sh"]
