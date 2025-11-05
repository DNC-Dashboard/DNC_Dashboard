#!/usr/bin/env bash
# Deploy script for dashboard.dncouncil.org
# Runs on the SERVER, called by GitHub Actions after rsync.
# It installs deps, migrates DB, collects static, and restarts Gunicorn.

set -Eeuo pipefail

APP="/home/dncouncil/apps/mydjango"
VENV="/home/dncouncil/venvs/mydjango"
PY="/usr/bin/python3.11"

log() { printf "\033[1;32m[%s]\033[0m %s\n" "$(date '+%F %T')" "$*"; }

log "Starting deploy"

# --- Ensure virtualenv -------------------------------------------------------
if [[ ! -d "$VENV" ]]; then
  log "Creating venv at $VENV"
  "$PY" -m venv "$VENV"
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"
log "Python: $(python -V)"
pip install --upgrade pip setuptools wheel >/dev/null

# --- Install Python dependencies --------------------------------------------
if [[ -f "$APP/requirements.txt" ]]; then
  log "Installing requirements.txt"
  pip install -r "$APP/requirements.txt"
else
  log "No requirements.txt found — skipping pip install"
fi

# --- Django management commands ---------------------------------------------
cd "$APP"

# If your project uses a .env file in $APP, Django-environ will read it.
# (We never rsync .env from GitHub; it lives only on the server.)

log "Applying migrations"
python manage.py migrate --noinput

log "Collecting static files"
python manage.py collectstatic --noinput

# --- Restart application -----------------------------------------------------
log "Restarting Gunicorn service"
sudo systemctl restart mydjango

# Optional: show a short status line
state="$(systemctl is-active mydjango || true)"
log "Gunicorn service state: ${state}"

log "Deploy OK"
