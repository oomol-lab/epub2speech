#!/usr/bin/env python3
"""
Pylint check script for the project
"""
import subprocess
import sys
from pathlib import Path


def run_pylint():
    """Run pylint on the entire project"""
    project_root = Path(__file__).parent.parent

    # Pylint configuration
    pylint_args = [
        "pylint",
        "--disable=missing-module-docstring,missing-class-docstring,missing-function-docstring",  # Reduce noise for now
        "--max-line-length=120",
        "--good-names=i,j,k,ex,Run,_,x,y,z",  # Allow common short names
        "--ignore=tests",  # Skip tests directory
        str(project_root / "epub2speech")
    ]

    print("Running pylint check...")
    result = subprocess.run(pylint_args, capture_output=True, text=True)

    if result.stdout:
        print("\nPylint output:")
        print(result.stdout)

    if result.stderr:
        print("\nPylint errors:")
        print(result.stderr)

    if result.returncode != 0:
        print(f"\nPylint check failed with exit code: {result.returncode}")
        return False
    else:
        print("Pylint check passed!")
        return True


if __name__ == "__main__":
    success = run_pylint()
    sys.exit(0 if success else 1)