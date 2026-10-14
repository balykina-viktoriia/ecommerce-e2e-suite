from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Mark every test with the name of its layer folder, so `pytest -m api` selects a layer."""
    for item in items:
        layer = Path(item.path).relative_to(TESTS_DIR).parts[0]
        item.add_marker(getattr(pytest.mark, layer))
