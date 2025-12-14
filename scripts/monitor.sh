#!/usr/bin/env bash
set -euo pipefail

echo "Viewing logs (press Ctrl+C to exit)"
docker-compose logs -f app
