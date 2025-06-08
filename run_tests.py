#!/usr/bin/env python3
"""
Test runner script for Silicon Automation MCP MongoDB Server

This script provides easy ways to run different types of tests:
- Unit tests
- Integration tests
- Performance tests
- All tests
- Coverage reports
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and handle errors"""
    if description:
        print(f"\n🔄 {description}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def setup_environment():
    """Set up the test environment"""
    # Add mcp_mongodb_server to Python path
    project_root = Path(__file__).parent
    mcp_path = project_root / "mcp_mongodb_server"
    
    current_path = os.environ.get("PYTHONPATH", "")
    if str(mcp_path) not in current_path:
        os.environ["PYTHONPATH"] = f"{current_path}:{mcp_path}"
    
    # Set default MongoDB URI for testing
    if "MONGODB_URI" not in os.environ:
        os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
    
    print(f"🔧 Environment setup complete")
    print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"   MONGODB_URI: {os.environ.get('MONGODB_URI')}")


def install_dependencies():
    """Install test dependencies"""
    test_requirements = Path("tests/requirements.txt")
    mcp_requirements = Path("mcp_mongodb_server/requirements.txt")
    
    commands = [
        ([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"),
    ]
    
    if test_requirements.exists():
        commands.append(([sys.executable, "-m", "pip", "install", "-r", str(test_requirements)], 
                        "Installing test dependencies"))
    
    if mcp_requirements.exists():
        commands.append(([sys.executable, "-m", "pip", "install", "-r", str(mcp_requirements)], 
                        "Installing MCP server dependencies"))
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    return True


def run_unit_tests():
    """Run unit tests only"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "not slow and not integration and not browser",
        "-v"
    ]
    return run_command(cmd, "Running unit tests")


def run_integration_tests():
    """Run integration tests"""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/",
        "-m", "integration",
        "-v"
    ]
    return run_command(cmd, "Running integration tests")


def run_performance_tests():
    """Run performance tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "slow or performance", 
        "-v"
    ]
    return run_command(cmd, "Running performance tests")


def run_all_tests():
    """Run all tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v"
    ]
    return run_command(cmd, "Running all tests")


def run_coverage_report():
    """Generate and display coverage report"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=mcp_mongodb_server",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "-v"
    ]
    success = run_command(cmd, "Generating coverage report")
    
    if success:
        print("\n📊 Coverage report generated!")
        print("   HTML report: htmlcov/index.html")
        print("   Terminal report shown above")
    
    return success


def run_lint():
    """Run code linting"""
    commands = [
        ([sys.executable, "-m", "flake8", "mcp_mongodb_server/", "tests/", 
          "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"], 
         "Running flake8 (critical errors)"),
        ([sys.executable, "-m", "flake8", "mcp_mongodb_server/", "tests/",
          "--count", "--exit-zero", "--max-complexity=10", "--max-line-length=127", "--statistics"],
         "Running flake8 (all checks)")
    ]
    
    all_success = True
    for cmd, desc in commands:
        try:
            if not run_command(cmd, desc):
                all_success = False
        except FileNotFoundError:
            print(f"⚠️  Skipping {desc} - flake8 not installed")
    
    return all_success


def check_mongodb():
    """Check if MongoDB is available"""
    try:
        import pymongo
        client = pymongo.MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))
        client.admin.command('ping')
        client.close()
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Make sure MongoDB is running on the configured URI")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for Silicon Automation MCP Server")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--check-db", action="store_true", help="Check MongoDB connection")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # If no specific flags, run unit tests by default
    if not any([args.install, args.unit, args.integration, args.performance, 
                args.coverage, args.lint, args.check_db, args.all]):
        args.unit = True
    
    print("🧪 Silicon Automation Test Runner")
    print("=" * 40)
    
    setup_environment()
    
    success = True
    
    if args.install:
        success &= install_dependencies()
    
    if args.check_db:
        success &= check_mongodb()
    
    if args.lint:
        success &= run_lint()
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.performance:
        success &= run_performance_tests()
    
    if args.coverage:
        success &= run_coverage_report()
    
    if args.all:
        success &= run_all_tests()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All operations completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()