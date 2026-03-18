#!/usr/bin/env python3
"""
Check if Context7 MCP server is properly configured.

Uses an ordered verification strategy:
1. Check if context7@claude-plugins-official plugin is installed and enabled
2. Verify MCP connectivity via `claude mcp list` (checks for plugin-backed MCP)

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

    # Step 1: Check if context7 plugin is installed and enabled
    try:
        result = subprocess.run(
            ["claude", "plugins", "list"],
            capture_output=True,
            text=True,
            check=False
        )

        plugin_found = False
        plugin_enabled = False
        for line in result.stdout.splitlines():
            if "context7@claude-plugins-official" in line:
                plugin_found = True
                # Check if enabled (look for ✔ enabled or similar)
                if "enabled" in line.lower() and "✔" in line:
                    plugin_enabled = True
                break

        if not plugin_found:
            print("[ERROR] Context7 plugin is not installed")
            print()
            print("Install it with:")
            print("  claude plugin install context7@claude-plugins-official")
            print()
            return False

        if not plugin_enabled:
            print("[ERROR] Context7 plugin is installed but not enabled")
            print()
            print("Enable it with:")
            print("  claude plugin enable context7@claude-plugins-official")
            print()
            return False

        print("[OK] Context7 plugin is installed and enabled")
        print()

    except Exception as e:
        print(f"[ERROR] Failed to check plugin status: {e}")
        return False

    # Step 2: Verify MCP connectivity
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            check=False
        )

        if "plugin:context7:context7" in result.stdout or "context7" in result.stdout.lower():
            print("[OK] Context7 MCP is connected")
            print()
            print("MCP Status:")
            print(result.stdout)
            return True
        else:
            print("[WARN] Context7 plugin is enabled but MCP is not connected")
            print()
            print("Troubleshooting steps:")
            print("  1. Try restarting Claude Code")
            print("  2. Verify plugin status: claude plugins list")
            print("  3. If issue persists, reinstall the plugin:")
            print("       claude plugin uninstall context7@claude-plugins-official")
            print("       claude plugin install context7@claude-plugins-official")
            print()
            return False

    except Exception as e:
        print(f"[ERROR] Failed to check MCP connectivity: {e}")
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
