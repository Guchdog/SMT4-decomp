"""Private integration fixtures are optional in a source-only checkout."""

import os
from pathlib import Path


def require_private_fixtures(testcase, *paths):
    if os.environ.get("SMT4_SKIP_PRIVATE_TESTS") == "1":
        testcase.skipTest("Private integration fixtures disabled by SMT4_SKIP_PRIVATE_TESTS=1")
    missing = [str(path) for path in paths if not Path(path).is_file()]
    if missing:
        testcase.skipTest("Private integration fixture unavailable: " + ", ".join(missing))
