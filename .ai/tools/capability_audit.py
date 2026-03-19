#!/usr/bin/env python3
"""Cross-platform capability audit for Claude and Codex adapters."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Fallback parser for a subset of YAML used by the manifest."""
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


def _entry_enabled_for_repo(entry: Dict[str, Any], is_template: bool) -> bool:
    if entry.get("template_only", False) and not is_template:
        return False
    return True


def _audit_project_skills(
    entries: List[Dict[str, Any]],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
) -> None:
    skills_root = repo_root / ".claude" / "skills"
    for entry in entries:
        if not _entry_enabled_for_repo(entry, is_template):
            continue

        skill_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        skill_md = skills_root / skill_id / "SKILL.md"

        available = skill_md.is_file()
        message = ""
        if not available:
            message = (
                f"Project skill '{skill_id}' not found.\n"
                f"  Expected: .claude/skills/{skill_id}/SKILL.md"
            )

        result.add(
            AuditEntry(
                category="project_skill",
                capability_id=skill_id,
                required=required,
                available=available,
                method="filesystem (.claude/skills/<id>/SKILL.md)",
                message=message,
            )
        )


def _audit_codex_skills(
    entries: List[Dict[str, Any]],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
) -> None:
    skills_root = repo_root / ".codex" / "skills"
    for entry in entries:
        if not _entry_enabled_for_repo(entry, is_template):
            continue

        skill_id = entry.get("id", "")
        required = bool(entry.get("required", False))
        skill_md = skills_root / skill_id / "SKILL.md"
        available = skill_md.is_file()
        message = ""
        if not available:
            message = (
                f"Codex skill '{skill_id}' not found.\n"
                f"  Expected: .codex/skills/{skill_id}/SKILL.md"
            )

        result.add(
            AuditEntry(
                category="codex_skill",
                capability_id=skill_id,
                required=required,
                available=available,
                method="filesystem (.codex/skills/<id>/SKILL.md)",
                message=message,
            )
        )


def _audit_repo_commands(
    entries: List[Dict[str, Any]],
    repo_root: Path,
    is_template: bool,
    result: AuditResult,
) -> None:
    for entry in entries:
        if not _entry_enabled_for_repo(entry, is_template):
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
    return _run(["claude", "mcp", "list"])


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

            lowered = raw.lower()
            available = "context7" in lowered
            message = ""
            if not available:
                message = "Context7 MCP not connected."
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

    raw_manifest = _load_manifest(manifest)
    normalized = _normalize_manifest(raw_manifest)

    common = normalized.get("common_requirements", {}) or {}
    platform_req = (
        normalized.get("platform_requirements", {}).get(platform, {}) or {}
    )

    result = AuditResult(platform=platform)
    is_template = _is_template_repo(repo_root)

    _audit_project_skills(common.get("project_skills", []), repo_root, is_template, result)
    _audit_repo_commands(common.get("repo_commands", []), repo_root, is_template, result)

    if platform == "claude":
        _audit_claude_plugins(platform_req.get("claude_plugins", []), result)
        _audit_claude_marketplaces(platform_req.get("claude_marketplaces", []), result)
        _audit_claude_plugin_skills(platform_req.get("claude_plugin_skills", []), result)

    if platform == "codex":
        _audit_codex_skills(platform_req.get("codex_skills", []), repo_root, is_template, result)
        _audit_repo_commands(platform_req.get("repo_commands", []), repo_root, is_template, result)

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
    return Path(__file__).resolve().parents[2]


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
