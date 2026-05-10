#!/usr/bin/env python3
"""Cross-platform capability audit for Claude and Codex adapters."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

Dict = dict
List = list

try:
    from .paths import resolve_repo_root
    from .project_profile import detect
except ImportError:
    from paths import resolve_repo_root
    from project_profile import detect


@dataclass
class AuditEntry:
    category: str
    capability_id: str
    required: bool
    available: bool
    method: str
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "category": self.category,
            "id": self.capability_id,
            "required": self.required,
            "available": self.available,
            "method": self.method,
        }
        if self.message:
            data["message"] = self.message
        return data


@dataclass
class AuditResult:
    passed: bool = True
    entries: List[AuditEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    platform: str = "codex"

    def add(self, entry: AuditEntry) -> None:
        self.entries.append(entry)
        if entry.required and not entry.available:
            self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "passed": self.passed,
            "entries": [entry.to_dict() for entry in self.entries],
            "errors": self.errors,
        }


def _run(args: List[str], timeout: int = 15) -> Optional[str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _load_manifest(path: Path) -> Dict[str, Any]:
    text = path.read_text()
    try:
        import yaml  # type: ignore[import-untyped]

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        if "common_requirements:" in text or "platform_requirements:" in text:
            raise RuntimeError(
                "PyYAML is required to parse capabilities manifest v2. "
                "Install with: pip install pyyaml"
            )
        if re.search(r"^\s*[^#\n]+:\s*[>|]", text, re.MULTILINE):
            print(
                "[WARN] PyYAML unavailable and manifest contains advanced YAML scalars; "
                "fallback parser may be incomplete.",
                file=sys.stderr,
            )
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Fallback parser for a subset of YAML used by the manifest.

    This parser supports flat list/dict structures only and is intended
    for constrained legacy compatibility when PyYAML is unavailable.
    """
    result: Dict[str, Any] = {}
    current_top: Optional[str] = None
    current_list: List[Dict[str, Any]] = []
    current_item: Optional[Dict[str, Any]] = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not raw_line[0].isspace() and stripped.endswith(":"):
            if current_top is not None:
                if current_item is not None:
                    current_list.append(current_item)
                result[current_top] = current_list
            current_top = stripped[:-1]
            current_list = []
            current_item = None
            continue

        if stripped.startswith("- "):
            if current_item is not None:
                current_list.append(current_item)
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                key, value = rest.split(":", 1)
                current_item[key.strip()] = _coerce(value.strip())
            continue

        if current_item is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_item[key.strip()] = _coerce(value.strip())

    if current_item is not None:
        current_list.append(current_item)
    if current_top is not None:
        result[current_top] = current_list

    return result


def _coerce(value: str) -> Any:
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def _is_template_repo(repo_root: Path) -> bool:
    return (repo_root / ".claude" / "skills" / "create-project").is_dir()


def _evaluate_when_selector(selector: str, profile: Any) -> bool:
    """Evaluate a when selector against a project profile.

    Supported syntax:
    - Single equality: "language=python"
    - List membership: "language in [python, cpp]"

    Args:
        selector: The when selector string
        profile: ProjectProfile object

    Returns:
        True if the selector matches the profile, False otherwise
    """
    if not selector or not profile:
        return True

    selector = selector.strip()

    # Empty selector after stripping whitespace
    if not selector:
        return True

    # Handle "axis in [value1, value2]" syntax
    if " in [" in selector:
        parts = selector.split(" in [", 1)
        if len(parts) != 2:
            return False

        axis = parts[0].strip()
        values_str = parts[1].rstrip("]").strip()
        allowed_values = {v.strip() for v in values_str.split(",") if v.strip()}

        # Get the profile axis value
        if axis == "language":
            profile_values = {lang.value for lang in profile.language}
            return bool(profile_values & allowed_values)
        elif axis == "build_system":
            return profile.build_system.value in allowed_values
        elif axis == "bindings":
            if profile.bindings:
                return profile.bindings.value in allowed_values
            return "none" in allowed_values
        elif axis == "distribution":
            if profile.distribution:
                return profile.distribution.value in allowed_values
            return "none" in allowed_values
        elif axis == "hardware_targets":
            profile_values = {hw.value for hw in profile.hardware_targets}
            return bool(profile_values & allowed_values)
        elif axis == "external_dependencies":
            if profile.external_dependencies:
                return profile.external_dependencies.value in allowed_values
            return "none" in allowed_values

        return False

    # Handle "axis=value" syntax
    if "=" in selector:
        axis, value = selector.split("=", 1)
        axis = axis.strip()
        value = value.strip()

        if axis == "language":
            return any(lang.value == value for lang in profile.language)
        elif axis == "build_system":
            return profile.build_system.value == value
        elif axis == "bindings":
            if profile.bindings:
                return profile.bindings.value == value
            return value == "none"
        elif axis == "distribution":
            if profile.distribution:
                return profile.distribution.value == value
            return value == "none"
        elif axis == "hardware_targets":
            return any(hw.value == value for hw in profile.hardware_targets)
        elif axis == "external_dependencies":
            if profile.external_dependencies:
                return profile.external_dependencies.value == value
            return value == "none"

        return False

    # Unknown selector format
    return False


def _normalize_manifest(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert legacy v1 and v2 manifest formats to a single v2-like structure."""
    if "common_requirements" in raw or "platform_requirements" in raw:
        common = raw.get("common_requirements", {}) or {}
        platforms = raw.get("platform_requirements", {}) or {}
        if not isinstance(common, dict):
            common = {}
        if not isinstance(platforms, dict):
            platforms = {}
        return {
            "common_requirements": common,
            "platform_requirements": platforms,
        }

    # Legacy v1 shape compatibility
    return {
        "common_requirements": {
            "project_skills": raw.get("project_skills", []),
        },
        "platform_requirements": {
            "claude": {
                "claude_plugins": raw.get("claude_plugins", []),
                "claude_marketplaces": raw.get("claude_marketplaces", []),
                "claude_plugin_skills": raw.get("claude_plugin_skills", []),
                "integrations": raw.get("integrations", []),
            },
            "codex": {
                "integrations": [],
            },
        },
    }


def _entry_enabled_for_repo(entry: Dict[str, Any], is_template: bool, repo_root: Path) -> bool:
    if entry.get("template_only", False) and not is_template:
        return False

    # New when selector takes precedence
    when_selector = entry.get("when")
    if when_selector:
        profile = detect(repo_root)
        if profile is None:
            # If we can't detect a profile, default to allowing the entry
            # (conservative approach for unknown projects)
            return True
        return _evaluate_when_selector(when_selector, profile)

    # Legacy project_types field for backward compatibility
    project_types = entry.get("project_types")
    if project_types:
        profile = detect(repo_root)
        if profile is None:
            return False

        # Convert profile to legacy project_type for comparison
        # Use primary language as the project type
        primary_lang = profile.language[0].value if profile.language else "unknown"

        if isinstance(project_types, str):
            allowed = {project_types}
        elif isinstance(project_types, list):
            allowed = {str(item) for item in project_types}
        else:
            allowed = set()

        if primary_lang not in allowed:
            return False

    return True


def _dedupe_entries_by_id(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate manifest entries by id, preferring later overrides."""
    ordered: List[Dict[str, Any]] = []
    index_by_id: Dict[str, int] = {}

    for raw_entry in entries:
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        entry_id = str(entry.get("id", "")).strip()

        if not entry_id:
            ordered.append(entry)
            continue

        existing_idx = index_by_id.get(entry_id)
        if existing_idx is None:
            index_by_id[entry_id] = len(ordered)
            ordered.append(entry)
        else:
            ordered[existing_idx] = entry

    return ordered


def _audit_project_skills(
    entries: List[Dict[str, Any]],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
) -> None:
    """Audit vendor-neutral skill manifests under .ai/skills/<id>/SKILL.md.

    For Claude Code we additionally verify that the .claude/skills/<id>/SKILL.md
    stub exists, since Claude relies on it for slash-command discovery.
    """
    ai_skills_root = repo_root / ".ai" / "skills"
    claude_skills_root = repo_root / ".claude" / "skills"
    is_claude_platform = result.platform == "claude"

    for entry in entries:
        if not _entry_enabled_for_repo(entry, is_template, repo_root):
            continue

        skill_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        template_only = bool(entry.get("template_only", False))

        # The canonical body lives at .ai/skills/<id>/SKILL.md for non-template
        # skills. Template-only skills (e.g. create-project) ship only on the
        # Claude side because they apply to the template repo, not generated
        # projects.
        if template_only:
            ai_skill_md = None
        else:
            ai_skill_md = ai_skills_root / skill_id / "SKILL.md"

        claude_skill_md = claude_skills_root / skill_id / "SKILL.md"

        ai_ok = ai_skill_md is None or ai_skill_md.is_file()
        claude_ok = (not is_claude_platform) or claude_skill_md.is_file()

        available = ai_ok and claude_ok
        message_parts: List[str] = []
        if ai_skill_md is not None and not ai_skill_md.is_file():
            message_parts.append(
                f"Skill body missing: .ai/skills/{skill_id}/SKILL.md"
            )
        if is_claude_platform and not claude_skill_md.is_file():
            message_parts.append(
                f"Claude skill stub missing: .claude/skills/{skill_id}/SKILL.md"
            )

        method = "filesystem (.ai/skills/<id>/SKILL.md"
        if is_claude_platform:
            method += " + .claude/skills/<id>/SKILL.md stub"
        method += ")"

        result.add(
            AuditEntry(
                category="project_skill",
                capability_id=skill_id,
                required=required,
                available=available,
                method=method,
                message="\n".join(message_parts),
            )
        )


def _audit_repo_commands(
    entries: List[Dict[str, Any]],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
) -> None:
    for entry in entries:
        if not _entry_enabled_for_repo(entry, is_template, repo_root):
            continue

        command_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        rel_path = entry.get("path", "")
        command_path = repo_root / rel_path

        available = command_path.is_file()
        message = ""
        if available and entry.get("executable", False):
            available = bool(command_path.stat().st_mode & 0o111)
            if not available:
                message = f"Command '{rel_path}' exists but is not executable."
        elif not available:
            message = f"Required command wrapper missing: {rel_path}"

        result.add(
            AuditEntry(
                category="repo_command",
                capability_id=command_id,
                required=required,
                available=available,
                method="filesystem (repo command wrapper)",
                message=message,
            )
        )


def _claude_plugins_list() -> Optional[str]:
    return _run(["claude", "plugins", "list"])


def _claude_plugins_list_json() -> Optional[List[Dict[str, Any]]]:
    raw = _run(["claude", "plugins", "list", "--json"])
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def _claude_mcp_list() -> Optional[str]:
    timeout = 45
    timeout_env = os.environ.get("AGENT_MCP_HEALTH_TIMEOUT_SEC", "").strip()
    if timeout_env:
        try:
            parsed = int(timeout_env)
            if parsed > 0:
                timeout = parsed
        except ValueError:
            pass
    return _run(["claude", "mcp", "list"], timeout=timeout)


def _parse_context7_health(raw: str) -> Dict[str, Any]:
    """Parse `claude mcp list` output for Context7 connectivity details."""
    lines = [line.strip() for line in raw.splitlines() if "context7" in line.lower()]
    if not lines:
        return {
            "found": False,
            "connected": False,
            "failed": False,
            "detail": "",
        }

    failed = False
    connected = False
    for line in lines:
        lowered = line.lower()
        if "failed to connect" in lowered or "✗" in line:
            failed = True
        if "✓" in line:
            connected = True
            continue
        if "connected" in lowered and "failed" not in lowered:
            connected = True

    return {
        "found": True,
        "connected": connected,
        "failed": failed,
        "detail": lines[0],
    }


def _context7_plugin_configured() -> Dict[str, Any]:
    """Inspect plugin metadata for Context7 MCP configuration fallback."""
    plugins = _claude_plugins_list_json()
    if plugins is None:
        return {
            "configured": False,
            "message": "Could not inspect plugin metadata via `claude plugins list --json`.",
        }

    for plugin in plugins:
        plugin_id = str(plugin.get("id", ""))
        if not plugin_id.startswith("context7@"):
            continue
        if not plugin.get("enabled", False):
            return {
                "configured": False,
                "message": f"Context7 plugin '{plugin_id}' is installed but disabled.",
            }

        mcp_servers = plugin.get("mcpServers")
        if isinstance(mcp_servers, dict) and "context7" in mcp_servers:
            return {
                "configured": True,
                "message": "Context7 plugin is enabled with MCP server metadata.",
            }

        return {
            "configured": True,
            "message": "Context7 plugin is enabled (MCP server metadata not exposed by this CLI version).",
        }

    return {
        "configured": False,
        "message": "Context7 plugin is not installed or not visible to Claude CLI.",
    }


def _discover_plugin_skills(plugin_id: str, install_path: str) -> List[str]:
    skills_dir = Path(install_path) / "skills"
    if not skills_dir.is_dir():
        return []

    discovered: List[str] = []
    plugin_name = plugin_id.split("@", 1)[0]
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        if (skill_dir / "SKILL.md").is_file():
            discovered.append(f"{plugin_name}:{skill_dir.name}")
    return discovered


def _audit_claude_plugins(entries: List[Dict[str, Any]], result: AuditResult) -> None:
    raw = _claude_plugins_list()
    if raw is None:
        result.errors.append("`claude plugins list` failed — Claude CLI unavailable?")
        for entry in entries:
            result.add(
                AuditEntry(
                    category="claude_plugin",
                    capability_id=entry.get("id", ""),
                    required=bool(entry.get("required", False)),
                    available=False,
                    method="claude plugins list (command failed)",
                    message="Could not run `claude plugins list`.",
                )
            )
        return

    output = raw.lower()
    for entry in entries:
        plugin_id = entry.get("id", "")
        required = bool(entry.get("required", False))

        found = plugin_id.lower() in output
        enabled = False
        if found:
            idx = output.find(plugin_id.lower())
            enabled = "enabled" in output[idx : idx + 300]

        available = found and enabled
        message = ""
        if not available:
            if not found:
                message = f"Install required plugin: claude plugin install {plugin_id}"
            else:
                message = f"Enable required plugin: claude plugin enable {plugin_id}"

        result.add(
            AuditEntry(
                category="claude_plugin",
                capability_id=plugin_id,
                required=required,
                available=available,
                method="claude plugins list",
                message=message,
            )
        )


def _audit_claude_marketplaces(entries: List[Dict[str, Any]], result: AuditResult) -> None:
    raw = _run(["claude", "plugin", "marketplace", "list"])
    if raw is None:
        for entry in entries:
            result.add(
                AuditEntry(
                    category="claude_marketplace",
                    capability_id=entry.get("id", ""),
                    required=bool(entry.get("required", False)),
                    available=False,
                    method="claude plugin marketplace list (command failed)",
                    message="Could not run `claude plugin marketplace list`.",
                )
            )
        return

    output = raw.lower()
    for entry in entries:
        marketplace_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        source = entry.get("source", "")
        available = marketplace_id.lower() in output
        message = ""
        if not available:
            message = f"Add marketplace: claude plugin marketplace add {source}"

        result.add(
            AuditEntry(
                category="claude_marketplace",
                capability_id=marketplace_id,
                required=required,
                available=available,
                method="claude plugin marketplace list",
                message=message,
            )
        )


def _audit_claude_plugin_skills(entries: List[Dict[str, Any]], result: AuditResult) -> None:
    plugins = _claude_plugins_list_json()

    if plugins is None:
        available_plugins = {
            entry.capability_id
            for entry in result.entries
            if entry.category == "claude_plugin" and entry.available
        }

        for entry in entries:
            skill_id = entry.get("id", "")
            plugin_id = entry.get("plugin", "")
            required = bool(entry.get("required", False))
            available = plugin_id in available_plugins
            message = ""
            if not available:
                message = f"Install and enable parent plugin: {plugin_id}"

            result.add(
                AuditEntry(
                    category="claude_plugin_skill",
                    capability_id=skill_id,
                    required=required,
                    available=available,
                    method="derived from plugin availability (fallback)",
                    message=message,
                )
            )
        return

    plugin_skill_map: Dict[str, List[str]] = {}
    for plugin in plugins:
        if not plugin.get("enabled", False):
            continue
        plugin_id = plugin.get("id", "")
        install_path = plugin.get("installPath", "")
        if plugin_id and install_path:
            plugin_skill_map[plugin_id] = _discover_plugin_skills(plugin_id, install_path)

    for entry in entries:
        skill_id = entry.get("id", "")
        plugin_id = entry.get("plugin", "")
        required = bool(entry.get("required", False))

        discovered = plugin_skill_map.get(plugin_id, [])
        available = skill_id in discovered
        message = ""
        if not available:
            if plugin_id not in plugin_skill_map:
                message = f"Plugin '{plugin_id}' missing or disabled."
            else:
                message = (
                    f"Skill '{skill_id}' not provided by plugin '{plugin_id}'."
                )

        result.add(
            AuditEntry(
                category="claude_plugin_skill",
                capability_id=skill_id,
                required=required,
                available=available,
                method=f"filesystem scan of plugin '{plugin_id}'",
                message=message,
            )
        )


def _audit_integrations(
    entries: List[Dict[str, Any]],
    result: AuditResult,
    platform: str,
) -> None:
    for entry in entries:
        integration_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        check_type = entry.get("check", "")

        if check_type == "mcp" and platform == "claude":
            raw = _claude_mcp_list()
            if raw is None:
                context7_fallback = integration_id == "context7-mcp"
                if context7_fallback:
                    plugin_status = _context7_plugin_configured()
                    configured = bool(plugin_status.get("configured", False))
                    message = str(plugin_status.get("message", ""))
                    result.add(
                        AuditEntry(
                            category="integration",
                            capability_id=integration_id,
                            required=required,
                            available=configured,
                            method="claude plugins list --json (fallback)",
                            message=(
                                "Could not run `claude mcp list`; using plugin configuration fallback. "
                                + message
                            ),
                        )
                    )
                    continue

                result.add(
                    AuditEntry(
                        category="integration",
                        capability_id=integration_id,
                        required=required,
                        available=False,
                        method="claude mcp list",
                        message="Could not run `claude mcp list`.",
                    )
                )
                continue

            if integration_id == "context7-mcp":
                health = _parse_context7_health(raw)
                if health["connected"]:
                    result.add(
                        AuditEntry(
                            category="integration",
                            capability_id=integration_id,
                            required=required,
                            available=True,
                            method="claude mcp list",
                            message=health["detail"],
                        )
                    )
                    continue

                plugin_status = _context7_plugin_configured()
                configured = bool(plugin_status.get("configured", False))
                plugin_message = str(plugin_status.get("message", ""))

                if health["found"] and health["failed"]:
                    result.add(
                        AuditEntry(
                            category="integration",
                            capability_id=integration_id,
                            required=required,
                            available=configured,
                            method="claude mcp list + plugin fallback",
                            message=(
                                f"Health probe reported disconnected: {health['detail']}. "
                                + plugin_message
                            ),
                        )
                    )
                    continue

                if health["found"]:
                    result.add(
                        AuditEntry(
                            category="integration",
                            capability_id=integration_id,
                            required=required,
                            available=True,
                            method="claude mcp list",
                            message=health["detail"],
                        )
                    )
                    continue

                result.add(
                    AuditEntry(
                        category="integration",
                        capability_id=integration_id,
                        required=required,
                        available=configured,
                        method="claude mcp list + plugin fallback",
                        message="No Context7 entry found in `claude mcp list`. " + plugin_message,
                    )
                )
                continue

            lowered = raw.lower()
            available = integration_id.lower() in lowered
            message = "" if available else f"{integration_id} MCP not connected."
            result.add(
                AuditEntry(
                    category="integration",
                    capability_id=integration_id,
                    required=required,
                    available=available,
                    method="claude mcp list",
                    message=message,
                )
            )
            continue

        if check_type == "command":
            command = entry.get("command", "")
            output = _run(["/bin/sh", "-lc", command]) if command else None
            available = output is not None
            message = ""
            if not available:
                message = f"Integration command failed: {command}"
            result.add(
                AuditEntry(
                    category="integration",
                    capability_id=integration_id,
                    required=required,
                    available=available,
                    method="command execution",
                    message=message,
                )
            )
            continue

        # Unknown checks are advisory for optional integrations and failure for required ones.
        result.add(
            AuditEntry(
                category="integration",
                capability_id=integration_id,
                required=required,
                available=not required,
                method=f"unknown check type '{check_type}'",
                message=(
                    "Unsupported integration check type in manifest."
                    if required
                    else ""
                ),
            )
        )


def run_audit(
    repo_root: Path,
    platform: Optional[str] = None,
    is_claude: Optional[bool] = None,
    verbose: bool = False,
    manifest_path: Optional[Path] = None,
) -> AuditResult:
    if platform is None:
        platform = "claude" if is_claude else "codex"
    platform = platform.lower()
    if platform not in {"claude", "codex"}:
        raise ValueError(f"Unsupported platform: {platform}")

    manifest = manifest_path or repo_root / ".ai" / "capabilities.yml"
    if not manifest.exists():
        result = AuditResult(passed=False, platform=platform)
        result.errors.append(f"Capability manifest not found: {manifest}")
        return result

    try:
        raw_manifest = _load_manifest(manifest)
    except Exception as exc:
        result = AuditResult(passed=False, platform=platform)
        result.errors.append(f"Failed to parse capability manifest: {exc}")
        return result
    normalized = _normalize_manifest(raw_manifest)

    common = normalized.get("common_requirements", {}) or {}
    platform_req = (
        normalized.get("platform_requirements", {}).get(platform, {}) or {}
    )

    result = AuditResult(platform=platform)
    is_template = _is_template_repo(repo_root)

    _audit_project_skills(common.get("project_skills", []), repo_root, is_template, result)
    repo_commands = _dedupe_entries_by_id(
        [
            *common.get("repo_commands", []),
            *platform_req.get("repo_commands", []),
        ]
    )
    _audit_repo_commands(repo_commands, repo_root, is_template, result)

    if platform == "claude":
        _audit_claude_plugins(platform_req.get("claude_plugins", []), result)
        _audit_claude_marketplaces(platform_req.get("claude_marketplaces", []), result)
        _audit_claude_plugin_skills(platform_req.get("claude_plugin_skills", []), result)

    _audit_integrations(common.get("integrations", []), result, platform)
    _audit_integrations(platform_req.get("integrations", []), result, platform)

    if verbose:
        print_audit_report(result)

    return result


def print_audit_report(result: AuditResult) -> None:
    separator = "=" * 70
    print(separator)
    print(f"CAPABILITY AUDIT ({result.platform.upper()})")
    print(separator)

    if result.errors:
        for error in result.errors:
            print(f"[ERROR] {error}")
        print()

    grouped: Dict[str, List[AuditEntry]] = {}
    for entry in result.entries:
        grouped.setdefault(entry.category, []).append(entry)

    for category in sorted(grouped.keys()):
        print(f"--- {category.replace('_', ' ').title()} ---")
        for entry in grouped[category]:
            status = "[OK]" if entry.available else ("[FAIL]" if entry.required else "[MISS]")
            print(f"  {status} {entry.capability_id}")
            if entry.message:
                for line in entry.message.splitlines():
                    print(f"       {line}")
        print()

    total = len(result.entries)
    ok = sum(1 for entry in result.entries if entry.available)
    missing_required = sum(
        1 for entry in result.entries if entry.required and not entry.available
    )

    print(separator)
    if result.passed:
        print(f"AUDIT PASSED ({ok}/{total} capabilities available)")
    else:
        print(f"AUDIT FAILED ({missing_required} required capability(ies) missing)")
    print(separator)


def _repo_root_from_here() -> Path:
    return resolve_repo_root(Path(__file__).resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-platform capability audit")
    parser.add_argument("--platform", choices=["claude", "codex"], default="codex")
    parser.add_argument(
        "--manifest",
        default=".ai/capabilities.yml",
        help="Path to capabilities manifest (default: .ai/capabilities.yml)",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--verbose", action="store_true", help="Print verbose report")
    args = parser.parse_args()

    repo_root = _repo_root_from_here()
    manifest = repo_root / args.manifest

    result = run_audit(
        repo_root=repo_root,
        platform=args.platform,
        verbose=args.verbose and not args.json,
        manifest_path=manifest,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not args.verbose:
        print_audit_report(result)

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
