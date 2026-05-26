#!/usr/bin/env sh
set -e

ROOT_DIR=$(dirname "$(dirname "$0")")
cd "$ROOT_DIR"

echo "Running tests..."
if command -v pytest >/dev/null 2>&1; then
  pytest -q
  TEST_EXIT=$?
else
  echo "pytest not found locally — running tests inside python:3.11-slim container"
  docker run --rm -v "$PWD":/app -w /app python:3.11-slim sh -c "pip install -r requirements.txt && pytest -q"
  TEST_EXIT=$?
fi

if [ $TEST_EXIT -ne 0 ]; then
  echo "Tests failed (exit code $TEST_EXIT). Aborting image build." >&2
  exit $TEST_EXIT
fi

echo "Tests passed. Building Docker image for service 'web'..."
docker compose build --no-cache web

echo "Docker image built successfully."
