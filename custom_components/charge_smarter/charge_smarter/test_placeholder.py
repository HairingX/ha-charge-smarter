"""Placeholder test.

Ensures the unittest discoverer finds at least one test so CI doesn't exit 5
(``NO TESTS RAN``) while the library is still a skeleton. Replace with real
tests as the library grows.
"""

import unittest


class TestPlaceholder(unittest.TestCase):
    def test_library_package_imports(self) -> None:
        """Smoke test: the pure-logic library package imports cleanly."""
        from custom_components.charge_smarter import charge_smarter  # noqa: F401
