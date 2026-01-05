#!/usr/bin/env python3
"""Start Claude Code Proxy server."""

import sys
import os

# Unset ANTHROPIC_API_KEY from shell environment if present
# This ensures .env file values take precedence
if 'ANTHROPIC_API_KEY' in os.environ:
    print(f"Note: Removing ANTHROPIC_API_KEY from shell environment")
    del os.environ['ANTHROPIC_API_KEY']

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    main()