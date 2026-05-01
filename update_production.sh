#!/bin/bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SERVICE_NAME="petrovich"
HEALTHCHECK_ATTEMPTS=30
HEALTHCHECK_DELAY=2

GUNICORN_BIND_PORT_VALUE="$(grep -E '^GUNICORN_BIND_PORT=' ".env" | tail -n 1 | cut -d '=' -f 2- | tr -d '"' || true)"
DEFAULT_HEALTHCHECK_URL="http://127.0.0.1:${GUNICORN_BIND_PORT_VALUE:-10010}/healthcheck"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-$DEFAULT_HEALTHCHECK_URL}"

echo "==> Cleaning local code"
git reset --hard HEAD
git clean -fd

echo "==> Fetching latest code"
git checkout master
git fetch origin
git pull --ff-only origin master

source .venv/bin/activate

uv sync

echo "==> Running Django checks"
python manage.py check

echo "==> Applying migrations"
python manage.py migrate --noinput

echo "==> Collecting static"
python manage.py collectstatic --noinput

echo "==> Restarting service"
sudo systemctl restart "$SERVICE_NAME"






echo "==> Waiting for service to become active"
for ((attempt=1; attempt<=HEALTHCHECK_ATTEMPTS; attempt++)); do
  if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    break
  fi

  if (( attempt == HEALTHCHECK_ATTEMPTS )); then
    echo "Service did not become active: $SERVICE_NAME" >&2
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 1
  fi

  sleep "$HEALTHCHECK_DELAY"
done

echo "==> Checking HTTP health endpoint"
for ((attempt=1; attempt<=HEALTHCHECK_ATTEMPTS; attempt++)); do
  if curl --silent --show-error --fail --max-time 5 "$HEALTHCHECK_URL" >/dev/null; then
    sudo systemctl status "$SERVICE_NAME" --no-pager
    break
  fi

  echo "Ожидаем, пока поднимется сервер ($attempt/$HEALTHCHECK_ATTEMPTS)"

  if (( attempt == HEALTHCHECK_ATTEMPTS )); then
    echo "Healthcheck failed: $HEALTHCHECK_URL" >&2
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 1
  fi

  sleep "$HEALTHCHECK_DELAY"
done

deactivate
