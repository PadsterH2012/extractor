#!/usr/bin/env python3
"""
Test runner for Priority 1 (Critical Core Functionality) tests.

This script runs the most important tests that validate core functionality:
- PDF processing and extraction
- AI game detection
- MongoDB operations

Usage:
    python tests/run_priority1_tests.py [options]

Options:
    --verbose: Enable verbose output
    --coverage: Generate coverage report
    --html: Generate HTML coverage report
    --fast: Skip slow tests
    --stop-on-first-failure: Stop on first test failure
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(args):
    """Run Priority 1 tests with specified options"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Priority 1 test files
    test_files = [
        "tests/test_pdf_processor.py",
        "tests/test_ai_game_detector.py", 
        "tests/test_mongodb_manager.py",
        "tests/test_isbn_extraction.py"  # Existing test
    ]
    
    # Add test files to command
    cmd.extend(test_files)
    
    # Add pytest options based on arguments
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=Modules", "--cov-report=term-missing"])
        
        if args.html:
            cmd.append("--cov-report=html:htmlcov")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.stop_on_first_failure:
        cmd.append("-x")
    
    # Add markers for Priority 1 tests
    cmd.extend(["-m", "unit or not slow"])
    
    # Run with colored output
    cmd.append("--color=yes")
    
    print("Running Priority 1 Tests...")
    print("Command:", " ".join(cmd))
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ["pytest", "pytest-cov"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing required packages:")
        for package in missing:
            print(f"  - {package}")
        print("\nInstall with: pip install " + " ".join(missing))
        return False
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Priority 1 tests for the Extractor project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/run_priority1_tests.py
    python tests/run_priority1_tests.py --verbose --coverage
    python tests/run_priority1_tests.py --fast --stop-on-first-failure
    python tests/run_priority1_tests.py --coverage --html
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose test output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true", 
        help="Generate code coverage report"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report (requires --coverage)"
    )
    
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Skip slow tests (marked with @pytest.mark.slow)"
    )
    
    parser.add_argument(
        "--stop-on-first-failure", "-x",
        action="store_true",
        help="Stop testing on first failure"
    )
    
    args = parser.parse_args()
    
    # Validate HTML option
    if args.html and not args.coverage:
        print("Error: --html requires --coverage")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check if we're in the right directory
    if not Path("Modules").exists():
        print("Error: Please run from the project root directory")
        print("Current directory should contain the 'Modules' folder")
        return 1
    
    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
