#!/usr/bin/env python3
"""
Test runner for Priority 2 (Essential Integration & Workflow) tests.

This script runs integration and workflow tests that validate component
interactions and complete user workflows:
- End-to-end extraction workflows
- Flask web application functionality
- Text quality enhancement features

Usage:
    python tests/run_priority2_tests.py [options]

Options:
    --verbose: Enable verbose output
    --coverage: Generate coverage report
    --html: Generate HTML coverage report
    --fast: Skip slow tests
    --stop-on-first-failure: Stop on first test failure
    --integration-only: Run only integration tests
    --web-only: Run only web UI tests
    --text-only: Run only text enhancement tests
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(args):
    """Run Priority 2 tests with specified options"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Priority 2 test files
    test_files = []
    
    if args.integration_only:
        test_files = ["tests/test_e2e_extraction.py"]
    elif args.web_only:
        test_files = ["tests/test_web_ui.py"]
    elif args.text_only:
        test_files = ["tests/test_text_quality_enhancer.py"]
    else:
        # All Priority 2 tests
        test_files = [
            "tests/test_e2e_extraction.py",
            "tests/test_web_ui.py", 
            "tests/test_text_quality_enhancer.py"
        ]
    
    # Add test files to command
    cmd.extend(test_files)
    
    # Add pytest options based on arguments
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=Modules", "--cov=ui", "--cov-report=term-missing"])
        
        if args.html:
            cmd.append("--cov-report=html:htmlcov")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.stop_on_first_failure:
        cmd.append("-x")
    
    # Add markers for Priority 2 tests
    cmd.extend(["-m", "integration or not slow"])
    
    # Run with colored output
    cmd.append("--color=yes")
    
    print("Running Priority 2 Tests (Essential Integration & Workflow)...")
    print("Command:", " ".join(cmd))
    print("=" * 70)
    
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
    required_packages = ["pytest", "pytest-cov", "flask"]
    missing = []
    
    for package in required_packages:
        try:
            if package == "flask":
                import flask
            else:
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


def check_test_environment():
    """Check if test environment is properly set up"""
    issues = []
    
    # Check for Flask app
    ui_app_path = Path("ui/app.py")
    if not ui_app_path.exists():
        issues.append("Flask app not found at ui/app.py")
    
    # Check for core modules
    modules_path = Path("Modules")
    if not modules_path.exists():
        issues.append("Modules directory not found")
    
    required_modules = [
        "pdf_processor.py",
        "text_quality_enhancer.py",
        "ai_game_detector.py",
        "mongodb_manager.py"
    ]
    
    for module in required_modules:
        if not (modules_path / module).exists():
            issues.append(f"Required module not found: Modules/{module}")
    
    if issues:
        print("Test environment issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Priority 2 tests for the Extractor project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
    End-to-End Extraction: Complete PDF → Analysis → Database workflows
    Flask Web UI: File upload, API endpoints, error handling
    Text Quality Enhancement: OCR cleanup, spell checking, quality metrics

Examples:
    python tests/run_priority2_tests.py
    python tests/run_priority2_tests.py --verbose --coverage
    python tests/run_priority2_tests.py --integration-only
    python tests/run_priority2_tests.py --web-only --fast
    python tests/run_priority2_tests.py --text-only --coverage --html
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
    
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only end-to-end integration tests"
    )
    
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run only Flask web UI tests"
    )
    
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Run only text quality enhancement tests"
    )
    
    args = parser.parse_args()
    
    # Validate HTML option
    if args.html and not args.coverage:
        print("Error: --html requires --coverage")
        return 1
    
    # Validate exclusive options
    exclusive_options = [args.integration_only, args.web_only, args.text_only]
    if sum(exclusive_options) > 1:
        print("Error: Only one of --integration-only, --web-only, --text-only can be specified")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check test environment
    if not check_test_environment():
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
