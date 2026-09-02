"""Evaluate the bounded Python constraints supported by environment checks."""

from __future__ import annotations

import re

Version = tuple[int, int, int]
VERSION_TOKEN = re.compile(
    r"^(?P<operator>>=|<=|==|=|>|<)?"
    r"(?P<major>0|[1-9][0-9]*)"
    r"(?:\.(?P<minor>0|[1-9][0-9]*))?"
    r"(?:\.(?P<patch>0|[1-9][0-9]*))?$"
)


def _parse_token(value: str) -> tuple[str, Version, int] | None:
    """Parse one comparison token and retain its declared precision."""
    match = VERSION_TOKEN.fullmatch(value.strip())
    if match is None:
        return None
    precision = (
        1
        + int(match.group("minor") is not None)
        + int(match.group("patch") is not None)
    )
    version = (
        int(match.group("major")),
        int(match.group("minor") or 0),
        int(match.group("patch") or 0),
    )
    return (match.group("operator") or "", version, precision)


def _upper_bound(version: Version, *, operator: str, precision: int) -> Version:
    """Return the exclusive upper bound for one Poetry caret or tilde token."""
    major, minor, _patch = version
    if operator == "~":
        if precision == 1:
            return (major + 1, 0, 0)
        return (major, minor + 1, 0)
    if major > 0:
        return (major + 1, 0, 0)
    if precision == 1:
        return (1, 0, 0)
    if minor > 0:
        return (0, minor + 1, 0)
    if precision == 2:
        return (0, 1, 0)
    return (0, 0, version[2] + 1)


def matches_python_constraint(version: str, constraint: str) -> bool:
    """Return whether a full Python version satisfies a bounded Poetry constraint."""
    parsed_version = _parse_token(version)
    if parsed_version is None or parsed_version[0]:
        return False
    selected = parsed_version[1]
    normalised = constraint.replace(" ", "")
    if not normalised:
        return False

    if normalised[0] in {"^", "~"}:
        if "," in normalised:
            return False
        parsed_constraint = _parse_token(normalised[1:])
        if parsed_constraint is None or parsed_constraint[0]:
            return False
        lower = parsed_constraint[1]
        upper = _upper_bound(
            lower, operator=normalised[0], precision=parsed_constraint[2]
        )
        return lower <= selected < upper

    for raw_token in normalised.split(","):
        parsed_constraint = _parse_token(raw_token)
        if parsed_constraint is None:
            return False
        operator, required, precision = parsed_constraint
        if operator in {"", "=", "=="}:
            if selected[:precision] != required[:precision]:
                return False
        elif not {
            ">=": selected >= required,
            ">": selected > required,
            "<=": selected <= required,
            "<": selected < required,
        }[operator]:
            return False
    return True
