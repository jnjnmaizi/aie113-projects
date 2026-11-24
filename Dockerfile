FROM python:3.12-slim AS dependencies
WORKDIR /build
COPY requirements.lock .
RUN pip install --no-cache-dir --prefix=/install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.lock

FROM python:3.12-slim AS model
COPY --from=dependencies /install /usr/local
WORKDIR /app
COPY model_manifest.json .
COPY scripts/download_model.py scripts/download_model.py
ENV HF_HOME=/tmp/model-cache DISABLE_SAFETENSORS_CONVERSION=1
RUN python scripts/download_model.py

FROM python:3.12-slim AS runtime
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
WORKDIR /app
COPY --from=dependencies /install /usr/local
COPY --from=model --chown=10001:10001 /app/artifacts/model /app/artifacts/model
COPY src/ src/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    BEAN_MODEL_DIR=/app/artifacts/model HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready', timeout=3)"
CMD ["uvicorn", "bean_vision.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
