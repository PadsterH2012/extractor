#!/bin/bash
# AI-Powered Extraction v3 Web UI Launcher

echo "🚀 Launching AI-Powered Extraction v3 Web UI"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "ui/app.py" ]; then
    echo "❌ Please run this script from the Extractionv3 directory:"
    echo "   cd /mnt/network_repo/rule_book/extraction tool/Extractionv3"
    echo "   ./ui/launch.sh"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    if [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please activate manually:"
        echo "   source /mnt/network_repo/rule_book/venv/bin/activate"
        exit 1
    fi
fi

# Start the UI
echo "🌐 Starting Web UI..."
echo "   Local:   http://localhost:5000"
echo "   Network: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📝 Quick Start:"
echo "   1. Upload a PDF file"
echo "   2. Select AI provider (Claude recommended)"
echo "   3. Analyze content"
echo "   4. Extract content"
echo "   5. Import to ChromaDB"
echo ""
echo "⚠️  Press Ctrl+C to stop the server"
echo "=============================================="

python ui/start_ui.py