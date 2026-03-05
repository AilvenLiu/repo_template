#!/usr/bin/env python3
"""
Standalone constraint validation command.
Can be run at any time to check for violations.
"""

import sys
from pathlib import Path

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'common'))
from validate_constraints import validate_all_constraints, print_violations


def main():
    print("Checking constraints...")
    print()

    violations = validate_all_constraints()
    print_violations(violations)

    # Exit with appropriate code
    critical_count = sum(1 for v in violations if v.severity == 'CRITICAL')
    if critical_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
