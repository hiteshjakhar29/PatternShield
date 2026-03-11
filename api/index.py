"""
Vercel serverless entry point for PatternShield.

Vercel's file-system routing: any file in api/ is auto-built as a
serverless function and served at its URL path. This file → /api/index.
vercel.json rewrites all traffic (/*) to here.

Why this pattern works:
  - Vercel detects api/index.py automatically (no 'builds' config needed)
  - Vercel uses api/requirements.txt to install dependencies
  - The Flask WSGI 'app' object is what Vercel wraps as the handler
  - sys.path is extended so all backend/ imports resolve correctly
"""
import os
import sys

# ── Add backend/ to the Python import path ────────────────────────────────────
# This file lives at repo_root/api/index.py; backend/ is at repo_root/backend/
_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

# ── Signal to config.py and app.py that we're on Vercel ──────────────────────
# Vercel sets VERCEL=1 automatically in deployed functions; this line ensures
# the flag is present even during local `vercel dev` testing.
os.environ.setdefault("VERCEL", "1")

# ── Import the Flask app (WSGI callable) ─────────────────────────────────────
# Vercel wraps any module-level object named `app` that is a WSGI callable.
from app import app  # noqa: E402 — must come after sys.path setup
