#!/usr/bin/env python3
"""
AI-Powered Extraction v3 Web UI Startup Script
Launches the web interface with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("✅ Flask installed successfully")

def check_extraction_dependencies():
    """Check if main extraction dependencies are available"""
    parent_dir = Path(__file__).parent.parent
    sys.path.append(str(parent_dir))

    try:
        from Modules.ai_game_detector import AIGameDetector
        from Modules.multi_collection_manager import MultiGameCollectionManager
        print("✅ Extraction modules are available")
        return True
    except ImportError as e:
        print(f"❌ Extraction modules not found: {e}")
        print("Please ensure you're running from the Extractionv3 directory")
        print("and that all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Environment Check:")

    # Check AI provider configurations
    if os.getenv('ANTHROPIC_API_KEY'):
        print("✅ Claude/Anthropic API key configured")
    else:
        print("⚠️  Claude/Anthropic API key not set (Mock AI will be used)")

    if os.getenv('OPENAI_API_KEY'):
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not set")

    if os.getenv('LOCAL_LLM_URL'):
        print("✅ Local LLM URL configured")
    else:
        print("⚠️  Local LLM URL not set")

    # Check ChromaDB (will be tested at runtime)
    print("ℹ️  ChromaDB connection will be tested when UI starts")

def main():
    """Main startup function"""
    print("🚀 Starting AI-Powered Extraction v3 Web UI")
    print("=" * 50)

    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "ui" / "app.py").exists():
        print("❌ Please run this script from the Extractionv3 directory:")
        print("   cd /mnt/network_repo/rule_book/extraction tool/Extractionv3")
        print("   python ui/start_ui.py")
        sys.exit(1)

    # Check dependencies
    print("\n📦 Checking Dependencies:")
    check_dependencies()

    if not check_extraction_dependencies():
        sys.exit(1)

    # Check environment
    check_environment()

    # Start the Flask application
    print("\n🌐 Starting Web Server:")
    print("   URL: http://localhost:5000")
    print("   URL: http://0.0.0.0:5000 (accessible from network)")
    print("\n📝 Usage:")
    print("   1. Upload a PDF file")
    print("   2. Select AI provider (Claude recommended)")
    print("   3. Analyze content")
    print("   4. Extract content")
    print("   5. Import to ChromaDB/MongoDB")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)

    # Change to UI directory and start Flask
    ui_dir = current_dir / "ui"
    os.chdir(ui_dir)

    try:
        from app import app
        # Disable reloader to avoid path issues
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Web UI. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
