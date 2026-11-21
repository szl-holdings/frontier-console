FROM python:3.11.18-slim-trixie@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535
WORKDIR /app
COPY requirements.lock .
RUN python -m pip install --disable-pip-version-check --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock && python -m pip check
COPY app.py ./app.py
COPY static ./static
EXPOSE 7860
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
