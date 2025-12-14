#!/usr/bin/env bash
set -euo pipefail

echo "🚀 PatternShield Production Setup"
echo "=================================="

read -rp "Select environment (development/production): " ENV
read -rp "Database host: " DB_HOST
read -rp "Database user: " DB_USER
read -sp "Database password: " DB_PASSWORD
printf "\n"
read -rp "Generate random API key? (y/n): " GEN_KEY
API_KEY=$(python - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)
if [[ ${GEN_KEY,,} != "y" ]]; then
  read -rp "Enter API key: " API_KEY
fi

cat > .env <<EOF_ENV
FLASK_ENV=${ENV}
SECRET_KEY=$(python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/patternshield
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=patternshield
ALLOWED_API_KEYS=${API_KEY}
EOF_ENV

echo "\nEnvironment file generated at .env"
echo "Installing dependencies..."
pip install -r backend/requirements.txt

echo "Running migrations (if configured)..."
if command -v alembic >/dev/null 2>&1; then
  alembic upgrade head || true
fi

echo "Setup complete!"
