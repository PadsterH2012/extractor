#!/usr/bin/env python3
"""
Extraction v3 Version Information
Provides version details for the application
"""

import datetime

# Version in semantic versioning format (MAJOR.MINOR.PATCH)
__version__ = "3.1.0"

# Build date in ISO format
__build_date__ = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

# These values would typically be set during CI/CD process
__commit_hash__ = "unknown"  # Git commit hash
__branch__ = "main"          # Git branch
__environment__ = "development"  # development, staging, production

# Function to get version information as a dictionary
def get_version_info():
    """Return version information as a dictionary"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "commit_hash": __commit_hash__,
        "branch": __branch__,
        "environment": __environment__
    }