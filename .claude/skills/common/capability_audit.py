#!/usr/bin/env python3
"""Capability audit utility.

Reads `.ai/capabilities.yml` and verifies that all required plugins, skills,
and integrations are available on the current machine. The audit is invoked
by the `/init` skill and its structured result is recorded in
`.claude/session_state.json`.

Design principles
-----------------
* **Deterministic** — uses live CLI output, not cached assumptions.
* **Vendor-aware** — Claude Code checks are strict; non-Claude agents get
  an advisory report and may continue with partial gaps.
* **Template-aware** — entries marked ``template_only: true`` are skipped
  when the repository is a generated project (i.e. when
  `.claude/skills/create-project` does not exist).
* **No mutation** — the audit never installs, enables, or configures
  anything.  It detects, reports, and fails where required.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Manifest loader (pure YAML subset — no PyYAML dependency)
# ---------------------------------------------------------------------------

def _load_manifest(path: Path) -> Dict[str, Any]:
    """Parse the capabilities manifest.

    Uses PyYAML when available; falls back to a minimal hand-rolled
    parser that handles the flat list-of-dicts structure used by the
    manifest.
    """
    text = path.read_text()
    try:
        import yaml  # type: ignore[import-untyped]
        return yaml.safe_load(text)
    except ImportError:
        pass
    return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Minimal YAML parser sufficient for the capabilities manifest.

    Handles top-level keys mapping to lists of single-level dicts.
    Does NOT handle arbitrary YAML — only the structure used in
    .ai/capabilities.yml.
    """
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: List[Dict[str, Any]] = []
    current_item: Optional[Dict[str, Any]] = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        # skip blanks and comments
        if not stripped or stripped.startswith("#"):
            continue

        # top-level key (no leading whitespace, ends with colon)
        if not raw_line[0].isspace() and stripped.endswith(":"):
            if current_key is not None:
                if current_item is not None:
                    current_list.append(current_item)
                result[current_key] = current_list
            current_key = stripped[:-1]
            current_list = []
            current_item = None
            continue

        # list item start
        if stripped.startswith("- "):
            if current_item is not None:
                current_list.append(current_item)
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                k, v = rest.split(":", 1)
                current_item[k.strip()] = _coerce(v.strip())
            continue

        # continuation of current item
        if current_item is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            val = v.strip()
            # Handle multi-line `>` folded scalars
            if val == ">":
                # next non-blank indented lines are continuation
                continue
            current_item[k.strip()] = _coerce(val)
            continue

    # flush
    if current_item is not None:
        current_list.append(current_item)
    if current_key is not None:
        result[current_key] = current_list

    return result


def _coerce(value: str) -> Any:
    """Coerce simple YAML scalar values."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    return value


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    """A single capability check result."""
    category: str        # e.g. "claude_plugin", "project_skill"
    capability_id: str   # e.g. "context7@claude-plugins-official"
    required: bool
    available: bool
    method: str          # how it was checked
    message: str = ""    # human-readable detail (especially on failure)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "category": self.category,
            "id": self.capability_id,
            "required": self.required,
            "available": self.available,
            "method": self.method,
        }
        if self.message:
            d["message"] = self.message
        return d


@dataclass
class AuditResult:
    """Aggregated audit outcome."""
    passed: bool = True
    entries: List[AuditEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add(self, entry: AuditEntry) -> None:
        self.entries.append(entry)
        if entry.required and not entry.available:
            self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "entries": [e.to_dict() for e in self.entries],
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def _run(args: List[str], timeout: int = 15) -> Optional[str]:
    """Run a command and return stdout, or None on failure."""
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if r.returncode == 0:
            return r.stdout
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _claude_plugins_list() -> Optional[str]:
    """Return raw output of `claude plugins list`."""
    return _run(["claude", "plugins", "list"])


def _claude_plugins_list_json() -> Optional[List[Dict[str, Any]]]:
    """Return parsed JSON output of `claude plugins list --json`."""
    raw = _run(["claude", "plugins", "list", "--json"])
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _claude_mcp_list() -> Optional[str]:
    """Return raw output of `claude mcp list`."""
    return _run(["claude", "mcp", "list"])


def _discover_plugin_skills(plugin_id: str, install_path: str) -> List[str]:
    """Discover skills provided by a plugin by scanning its install directory.

    Returns list of skill IDs in the format "plugin-name:skill-name".
    """
    skills_dir = Path(install_path) / "skills"
    if not skills_dir.is_dir():
        return []

    discovered = []
    plugin_name = plugin_id.split("@")[0]  # Extract name from "name@source"

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            skill_name = skill_dir.name
            discovered.append(f"{plugin_name}:{skill_name}")

    return discovered


def _is_template_repo(repo_root: Path) -> bool:
    """True when running inside the template repository itself."""
    return (repo_root / ".claude" / "skills" / "create-project").is_dir()


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------

def run_audit(
    repo_root: Path,
    is_claude: bool = True,
    verbose: bool = False,
) -> AuditResult:
    """Execute the full capability audit.

    Parameters
    ----------
    repo_root:
        Repository root directory.
    is_claude:
        True when running inside Claude Code.  False for non-Claude agents.
    verbose:
        Print detailed progress.
    """
    manifest_path = repo_root / ".ai" / "capabilities.yml"
    if not manifest_path.exists():
        result = AuditResult(passed=False)
        result.errors.append(
            f"Capability manifest not found: {manifest_path.relative_to(repo_root)}"
        )
        return result

    manifest = _load_manifest(manifest_path)
    is_template = _is_template_repo(repo_root)
    result = AuditResult()

    if is_claude:
        _audit_claude_plugins(manifest, result, verbose)
        _audit_claude_marketplaces(manifest, result, verbose)
        _audit_claude_plugin_skills(manifest, result, verbose)
        _audit_integrations(manifest, result, verbose)

    _audit_project_skills(manifest, repo_root, is_template, result, verbose)

    return result


def _audit_claude_plugins(
    manifest: Dict[str, Any],
    result: AuditResult,
    verbose: bool,
) -> None:
    """Check that required Claude plugins are installed and enabled."""
    raw = _claude_plugins_list()
    if raw is None:
        result.errors.append(
            "`claude plugins list` failed — is Claude Code installed?"
        )
        # Mark all as unavailable
        for entry in manifest.get("claude_plugins", []):
            result.add(AuditEntry(
                category="claude_plugin",
                capability_id=entry["id"],
                required=entry.get("required", False),
                available=False,
                method="claude plugins list (command failed)",
                message="Could not run `claude plugins list`.",
            ))
        return

    raw_lower = raw.lower()
    for entry in manifest.get("claude_plugins", []):
        plugin_id = entry["id"]
        required = entry.get("required", False)
        # The output format is "  > name@source\n  ... Status: * enabled"
        # We check for the plugin id appearing in the output
        found = plugin_id.lower() in raw_lower
        # Also check enabled status if found
        enabled = False
        if found:
            # Find the block for this plugin and check for "enabled"
            idx = raw_lower.find(plugin_id.lower())
            block = raw_lower[idx:idx + 300]
            enabled = "enabled" in block

        available = found and enabled
        msg = ""
        if not available:
            if not found:
                msg = (
                    f"Plugin '{plugin_id}' is not installed.\n"
                    f"  Install it: claude plugin install {plugin_id}"
                )
            else:
                msg = (
                    f"Plugin '{plugin_id}' is installed but not enabled.\n"
                    f"  Enable it: claude plugin enable {plugin_id}"
                )
        result.add(AuditEntry(
            category="claude_plugin",
            capability_id=plugin_id,
            required=required,
            available=available,
            method="claude plugins list",
            message=msg,
        ))


def _audit_claude_marketplaces(
    manifest: Dict[str, Any],
    result: AuditResult,
    verbose: bool,
) -> None:
    """Check that required marketplace sources are configured."""
    raw = _run(["claude", "plugin", "marketplace", "list"])
    if raw is None:
        for entry in manifest.get("claude_marketplaces", []):
            result.add(AuditEntry(
                category="claude_marketplace",
                capability_id=entry["id"],
                required=entry.get("required", False),
                available=False,
                method="claude plugin marketplace list (command failed)",
                message="Could not run `claude plugin marketplace list`.",
            ))
        return

    raw_lower = raw.lower()
    for entry in manifest.get("claude_marketplaces", []):
        mkt_id = entry["id"]
        required = entry.get("required", False)
        available = mkt_id.lower() in raw_lower
        msg = ""
        if not available:
            source = entry.get("source", "")
            msg = (
                f"Marketplace '{mkt_id}' is not configured.\n"
                f"  Add it: claude plugin marketplace add {source}"
            )
        result.add(AuditEntry(
            category="claude_marketplace",
            capability_id=mkt_id,
            required=required,
            available=available,
            method="claude plugin marketplace list",
            message=msg,
        ))


def _audit_claude_plugin_skills(
    manifest: Dict[str, Any],
    result: AuditResult,
    verbose: bool,
) -> None:
    """Check that required plugin-provided skills are available.

    Plugin skills are discovered by scanning the plugin's install directory
    for skills/*/SKILL.md files. This is deterministic and does not assume
    all declared skills are available just because the plugin is installed.
    """
    # Get plugin metadata with install paths
    plugins_json = _claude_plugins_list_json()
    if plugins_json is None:
        # Fall back to checking if parent plugin is available
        available_plugins: set = set()
        for e in result.entries:
            if e.category == "claude_plugin" and e.available:
                available_plugins.add(e.capability_id)

        for entry in manifest.get("claude_plugin_skills", []):
            skill_id = entry["id"]
            required = entry.get("required", False)
            parent_plugin = entry.get("plugin", "")
            available = parent_plugin in available_plugins
            msg = ""
            if not available:
                msg = (
                    f"Plugin skill '{skill_id}' is unavailable because its parent "
                    f"plugin '{parent_plugin}' is not installed/enabled.\n"
                    f"  Install the plugin: claude plugin install {parent_plugin}"
                )
            result.add(AuditEntry(
                category="claude_plugin_skill",
                capability_id=skill_id,
                required=required,
                available=available,
                method=f"derived from plugin '{parent_plugin}' availability (fallback)",
                message=msg,
            ))
        return

    # Build map of plugin_id -> discovered skills
    plugin_skills_map: Dict[str, List[str]] = {}
    for plugin_data in plugins_json:
        if not plugin_data.get("enabled", False):
            continue
        plugin_id = plugin_data.get("id", "")
        install_path = plugin_data.get("installPath", "")
        if plugin_id and install_path:
            discovered = _discover_plugin_skills(plugin_id, install_path)
            plugin_skills_map[plugin_id] = discovered

    # Check each required plugin skill
    for entry in manifest.get("claude_plugin_skills", []):
        skill_id = entry["id"]
        required = entry.get("required", False)
        parent_plugin = entry.get("plugin", "")

        # Check if skill is actually discovered
        discovered_skills = plugin_skills_map.get(parent_plugin, [])
        available = skill_id in discovered_skills

        msg = ""
        if not available:
            if parent_plugin not in plugin_skills_map:
                msg = (
                    f"Plugin skill '{skill_id}' is unavailable because its parent "
                    f"plugin '{parent_plugin}' is not installed/enabled.\n"
                    f"  Install the plugin: claude plugin install {parent_plugin}"
                )
            else:
                msg = (
                    f"Plugin skill '{skill_id}' is not provided by plugin '{parent_plugin}'.\n"
                    f"  The plugin is installed but does not expose this skill.\n"
                    f"  Discovered skills: {', '.join(discovered_skills) if discovered_skills else '(none)'}"
                )

        result.add(AuditEntry(
            category="claude_plugin_skill",
            capability_id=skill_id,
            required=required,
            available=available,
            method=f"filesystem scan of plugin '{parent_plugin}' install directory",
            message=msg,
        ))


def _audit_project_skills(
    manifest: Dict[str, Any],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
    verbose: bool,
) -> None:
    """Check that required project skills exist under .claude/skills/."""
    skills_dir = repo_root / ".claude" / "skills"
    for entry in manifest.get("project_skills", []):
        skill_id = entry["id"]
        required = entry.get("required", False)

        # Template-only skills are not required in generated projects
        if entry.get("template_only", False) and not is_template:
            if verbose:
                print(f"  [SKIP] {skill_id} (template_only, this is a generated project)")
            continue

        skill_dir = skills_dir / skill_id
        skill_md = skill_dir / "SKILL.md"
        available = skill_md.is_file()
        msg = ""
        if not available:
            if not skill_dir.is_dir():
                msg = (
                    f"Project skill '{skill_id}' not found.\n"
                    f"  Expected directory: .claude/skills/{skill_id}/\n"
                    f"  Copy it from the template repository."
                )
            else:
                msg = (
                    f"Project skill '{skill_id}' exists but has no SKILL.md.\n"
                    f"  Create .claude/skills/{skill_id}/SKILL.md with valid frontmatter."
                )
        result.add(AuditEntry(
            category="project_skill",
            capability_id=skill_id,
            required=required,
            available=available,
            method="filesystem (.claude/skills/<id>/SKILL.md)",
            message=msg,
        ))


def _audit_integrations(
    manifest: Dict[str, Any],
    result: AuditResult,
    verbose: bool,
) -> None:
    """Check special integrations (e.g. Context7 MCP health)."""
    for entry in manifest.get("integrations", []):
        integration_id = entry["id"]
        required = entry.get("required", False)
        check_type = entry.get("check", "")

        if check_type == "mcp":
            raw = _claude_mcp_list()
            available = False
            msg = ""
            if raw is None:
                msg = (
                    "Could not run `claude mcp list`.\n"
                    "  Ensure Claude Code is installed and the MCP subsystem is available."
                )
            elif "context7" in raw.lower():
                available = True
            else:
                msg = (
                    "Context7 MCP server is not configured.\n"
                    "  Add it with:\n"
                    "    claude mcp add context7 -- npx -y @anthropic-ai/context7-mcp@latest"
                )
            result.add(AuditEntry(
                category="integration",
                capability_id=integration_id,
                required=required,
                available=available,
                method="claude mcp list",
                message=msg,
            ))
        else:
            # Unknown check type — report as unavailable
            result.add(AuditEntry(
                category="integration",
                capability_id=integration_id,
                required=required,
                available=False,
                method=f"unknown check type '{check_type}'",
                message=f"Unsupported check type '{check_type}' in manifest.",
            ))


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------

def print_audit_report(result: AuditResult) -> None:
    """Print a human-readable audit report."""
    sep = "=" * 70

    print()
    print(sep)
    print("CAPABILITY AUDIT")
    print(sep)
    print()

    if result.errors:
        for err in result.errors:
            print(f"[ERROR] {err}")
        print()

    # Group by category
    categories = {}
    for e in result.entries:
        categories.setdefault(e.category, []).append(e)

    category_labels = {
        "claude_plugin": "Claude Plugins",
        "claude_marketplace": "Claude Marketplaces",
        "claude_plugin_skill": "Claude Plugin Skills",
        "project_skill": "Project Skills",
        "integration": "Integrations",
    }

    for cat_key, label in category_labels.items():
        entries = categories.get(cat_key, [])
        if not entries:
            continue

        print(f"--- {label} ---")
        for e in entries:
            status = "[OK]" if e.available else ("[FAIL]" if e.required else "[MISS]")
            print(f"  {status} {e.capability_id}")
            if e.message:
                for line in e.message.strip().splitlines():
                    print(f"       {line}")
        print()

    # Summary
    total = len(result.entries)
    ok = sum(1 for e in result.entries if e.available)
    req_missing = sum(
        1 for e in result.entries if e.required and not e.available
    )

    print(sep)
    if result.passed:
        print(f"AUDIT PASSED  ({ok}/{total} capabilities available)")
    else:
        print(f"AUDIT FAILED  ({req_missing} required capability(ies) missing)")
        print()
        print("The session is BLOCKED. Fix the issues above and re-run /init.")
    print(sep)
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the capability audit as a standalone script."""
    import argparse
    parser = argparse.ArgumentParser(description="Capability audit")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument(
        "--agent",
        choices=["claude", "other"],
        default="claude",
        help="Agent type (claude runs strict checks; other runs advisory)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    is_claude = args.agent == "claude"
    result = run_audit(repo_root, is_claude=is_claude, verbose=args.verbose)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_audit_report(result)

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
