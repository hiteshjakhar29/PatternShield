#!/bin/bash
# PatternShield v2.0 — Mac Setup & Run Script
# Usage: chmod +x setup.sh && ./setup.sh

set -e

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🛡️  PatternShield v2.0 — Setup"
echo "═══════════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Install: brew install python3"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# Create venv
if [ ! -d "backend/venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv backend/venv
fi

echo "→ Activating venv & installing deps..."
source backend/venv/bin/activate
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

# Download NLTK data
python3 -c "
import nltk, os
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
try: nltk.download('punkt_tab', quiet=True)
except: pass
print('✅ NLTK data ready')
"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🚀 Starting PatternShield API..."
echo "═══════════════════════════════════════════════════"
echo ""
echo "  API:        http://localhost:5000"
echo "  Health:     http://localhost:5000/health"
echo "  Test page:  Open chrome-extension/test-page.html"
echo ""
echo "  To run tests (in another terminal):"
echo "    source backend/venv/bin/activate"
echo "    python backend/test_production.py"
echo ""
echo "  Chrome Extension:"
echo "    1. Open chrome://extensions"
echo "    2. Enable Developer Mode"
echo "    3. Click 'Load unpacked' → select chrome-extension/"
echo "    4. Open test-page.html and click the extension icon"
echo ""
echo "  Press Ctrl+C to stop."
echo "═══════════════════════════════════════════════════"
echo ""

cd backend
python3 app.py
