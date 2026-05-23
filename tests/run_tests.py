#!/usr/bin/env python
"""
BoxLang Sublime Text Package — Test Runner

A TestBox-inspired test runner that provides multiple ways to execute the test suite.

Usage:
    python tests/run_tests.py [options]

Options:
    --unit          Run only unit tests
    --integration   Run only integration tests
    --verbose       Verbose output
    --coverage      Run with coverage reporting
    --watch         Watch mode (re-run on file changes)
    --report        Generate HTML coverage report
    --marker MARKER Run tests with specific pytest marker
    --file FILE     Run specific test file
    --help          Show this help message
"""

import sys
import os
import argparse
import subprocess

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Banner
BANNER = f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗
║          BoxLang Sublime Text — Test Runner            ║
╚══════════════════════════════════════════════════════════╝{RESET}
"""


def print_banner():
    """Print the test runner banner."""
    print(BANNER)


def print_header(text):
    """Print a section header."""
    print(f"\n{BOLD}{BLUE}── {text} {'─' * (60 - len(text) - 4)}{RESET}")


def print_result(success, message):
    """Print a test result."""
    color = GREEN if success else RED
    symbol = "✓" if success else "✗"
    print(f"  {color}{symbol} {message}{RESET}")


def run_tests(args):
    """Run the test suite with the given arguments."""
    cmd = [sys.executable, "-m", "pytest"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage or args.report:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])

    if args.report:
        cmd.append("--cov-report=html:tests/coverage_html")

    if args.marker:
        cmd.extend(["-m", args.marker])

    if args.file:
        cmd.append(args.file)
    elif args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.append("tests/integration/")
    else:
        cmd.append("tests/")

    if args.watch:
        cmd.append("--watch")

    print_header("Running Tests")
    print(f"  Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print_header("Results")
    if result.returncode == 0:
        print_result(True, "All tests passed!")
    else:
        print_result(False, f"Some tests failed (exit code: {result.returncode})")

    if args.report:
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coverage_html", "index.html")
        print(f"\n  {YELLOW}Coverage report:{RESET} {report_path}")

    return result.returncode


def run_single_test(test_path):
    """Run a single test file or test function."""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return result.returncode


def list_tests():
    """List all available tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"]
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BoxLang Sublime Text Package — Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py                  Run all tests
  python tests/run_tests.py --unit           Run unit tests only
  python tests/run_tests.py --coverage       Run with coverage
  python tests/run_tests.py --verbose        Verbose output
  python tests/run_tests.py --report         Generate HTML coverage report
  python tests/run_tests.py --marker fast    Run fast tests only
  python tests/run_tests.py --file tests/unit/test_ast_parser.py
        """
    )

    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--watch", action="store_true", help="Watch mode (requires pytest-watch)")
    parser.add_argument("--report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--marker", "-m", type=str, help="Run tests with specific pytest marker")
    parser.add_argument("--file", "-f", type=str, help="Run specific test file")
    parser.add_argument("--list", action="store_true", help="List all available tests")

    args = parser.parse_args()

    print_banner()

    if args.list:
        return list_tests()

    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
