import sys
from pathlib import Path

# Add project root to sys.path so tests can import backend and simulation modules
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import pytest
from backend.core.schema_migrator import init_db_schema


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """
    Hermetic test database initializer.
    Guarantees all 19 relational and time-series tables plus authoritative
    corridor entities are seeded before any test suite executes, preventing
    alphabetical execution order bugs and clean CI checkout failures.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.run_until_complete(init_db_schema())
    else:
        asyncio.run(init_db_schema())
