#!/usr/bin/env python3
"""
Check if Context7 MCP server is properly configured.

Usage:
    python3 .claude/skills/context7/scripts/check_mcp.py
"""

import subprocess
import sys
from pathlib import Path


def check_mcp_server():
    """Check if Context7 MCP server is configured."""
    print("=" * 70)
    print("CONTEXT7 MCP SERVER VERIFICATION")
    print("=" * 70)
    print()

    # Check if claude CLI is available
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("[ERROR] Claude CLI not found")
            print("Install Claude Code first: https://code.claude.com")
            return False
    except FileNotFoundError:
        print("[ERROR] Claude CLI not found")
        print("Install Claude Code first: https://code.claude.com")
        return False

    print("[OK] Claude CLI is installed")
    print()

    # List MCP servers
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            check=False
        )

        if "context7" in result.stdout.lower():
            print("[OK] Context7 MCP server is configured")
            print()
            print("MCP Servers:")
            print(result.stdout)
            return True
        else:
            print("[WARN] Context7 MCP server not found")
            print()
            print("To add Context7, run:")
            print()
            print('  claude mcp add --transport http context7 \\')
            print('    https://mcp.context7.com/mcp \\')
            print('    --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"')
            print()
            return False

    except Exception as e:
        print(f"[ERROR] Failed to check MCP servers: {e}")
        return False


def main():
    """Main entry point."""
    success = check_mcp_server()

    print("=" * 70)
    if success:
        print("Context7 is ready to use!")
    else:
        print("Context7 setup required. Follow instructions above.")
    print("=" * 70)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
