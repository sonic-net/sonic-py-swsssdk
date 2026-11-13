"""Run the unmodified upstream suite with Bazel-managed Python and reports."""

import os
from pathlib import Path
import sys

import pytest


if __name__ == "__main__":
    source = Path(__file__).absolute().parent
    reports = Path(os.environ["TEST_UNDECLARED_OUTPUTS_DIR"])
    # The upstream deprecation test invokes python3 by name in a subprocess.
    os.environ["PATH"] = str(Path(sys.executable).parent)
    os.environ["PYTHONPATH"] = os.pathsep.join([str(source / "src"), os.environ.get("PYTHONPATH", "")])
    os.environ["COVERAGE_FILE"] = str(reports / ".coverage")
    os.chdir(source)
    # Keep the configured coverage reports and verbosity; only move report files
    # out of the input runfiles tree into Bazel's writable test output directory.
    sys.exit(pytest.main([
        "-c", str(source / "pytest.ini"),
        # Directory matching fails across Bazel file symlinks; this is the same
        # source package selected by upstream --cov=src.
        "--cov-reset", "--cov=swsssdk",
        "--cov-report=",
        "--cov-report=html:" + str(reports / "htmlcov"),
        "--cov-report=term",
        "--cov-report=xml:" + str(reports / "coverage.xml"),
        "--junitxml=" + str(reports / "test-results.xml"),
        "-o", "cache_dir=" + os.environ["TEST_TMPDIR"] + "/pytest_cache",
        str(source / "test"),
        *sys.argv[1:],
    ]))
