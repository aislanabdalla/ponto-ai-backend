FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    INSIGHTFACE_HOME=/models

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Pré-baixa os modelos do InsightFace para evitar lentidão no 1º uso
RUN python - <<'PY'\nfrom insightface.app import FaceAnalysis\nimport os\napp=FaceAnalysis(name="buffalo_l", root=os.environ.get("INSIGHTFACE_HOME","/models"))\napp.prepare(ctx_id=0, det_size=(640,640))\nprint("models ready")\nPY

COPY . /app/
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
