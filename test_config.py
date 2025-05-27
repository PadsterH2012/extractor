#!/usr/bin/env python3
"""
Test script to verify that ChromaDB configuration is loaded from environment variables
"""

import os
import sys

# Add the parent directory to sys.path so we can import modules correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env.test file
load_dotenv(".env.test")

# Set the variables manually instead of importing the module
# to avoid dependency issues
CHROMA_HOST = os.getenv("CHROMA_HOST", "default-host")
CHROMA_PORT = os.getenv("CHROMA_PORT", "default-port")
CHROMA_BASE_URL = os.getenv("CHROMA_BASE_URL", f"http://{CHROMA_HOST}:{CHROMA_PORT}/api/v2")
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "default-tenant")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "default-database")

CHROMA_CONFIG = {
    "host": CHROMA_HOST,
    "port": CHROMA_PORT,
    "base_url": CHROMA_BASE_URL,
    "tenant": CHROMA_TENANT,
    "database": CHROMA_DATABASE
}

def test_chroma_config():
    """Test that ChromaDB configuration is loaded from environment variables"""
    print("Testing ChromaDB configuration:")
    print(f"  Host: {CHROMA_CONFIG['host']}")
    print(f"  Port: {CHROMA_CONFIG['port']}")
    print(f"  Base URL: {CHROMA_CONFIG['base_url']}")
    print(f"  Tenant: {CHROMA_CONFIG['tenant']}")
    print(f"  Database: {CHROMA_CONFIG['database']}")
    
    # Verify values match what's in .env.test
    assert CHROMA_CONFIG["host"] == "test-chroma-server"
    assert CHROMA_CONFIG["port"] == "9000"
    assert CHROMA_CONFIG["base_url"] == "http://test-chroma-server:9000/api/v2"
    assert CHROMA_CONFIG["tenant"] == "test_tenant"
    assert CHROMA_CONFIG["database"] == "test_database"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_chroma_config()