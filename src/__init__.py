"""Claude Code Proxy

A proxy server that enables Claude Code to work with OpenAI-compatible API providers.
"""

from dotenv import load_dotenv

# Load environment variables from .env file
# override=True ensures .env values take precedence over shell environment
load_dotenv(override=True)
__version__ = "1.0.0"
__author__ = "Claude Code Proxy"
