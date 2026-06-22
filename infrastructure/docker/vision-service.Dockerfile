FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app/apps/vision-service

# libglib2.0-0/libsm6/libxext6/libxrender1: runtime libs opencv-python-headless
# still links against for image decoding. libgomp1: onnxruntime threading.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc curl \
        libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/vision-service/ ./

RUN pip install --upgrade pip \
    && pip install -e .

# insightface downloads model weights here on first run — mounted as a
# named volume in docker-compose.yml so re-creating the container doesn't
# re-download them.
RUN mkdir -p /app/.insightface

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
