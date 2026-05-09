#!/usr/bin/env python3
"""Shared constants for policy and workflow enforcement."""

PROTECTED_BRANCHES = {"master", "main", "develop"}
PROTECTED_PREFIXES = ("release/", "hotfix/")

# Denylist for sensitive files in explicit commit staging.
SENSITIVE_PATH_PATTERNS = (
    r"(^|/)\.env(\.|$)",
    r"(^|/)credentials(\.|$|_)",
    r"\.(pem|key)$",
)
