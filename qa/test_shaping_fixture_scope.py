"""A variable-only fixture must not hide missing static or mixed expectations."""

import unittest

from qa.update_shaping_test_data import has_only_variable_expectations


class FixtureScopeTests(unittest.TestCase):
    def test_variable_only(self):
        self.assertTrue(
            has_only_variable_expectations(
                {
                    "variable.ttf": {"wght=400": ["glyph"]},
                }
            )
        )

    def test_empty_is_not_variable_only(self):
        self.assertFalse(has_only_variable_expectations({}))

    def test_static_is_not_variable_only(self):
        self.assertFalse(has_only_variable_expectations({"static.ttf": ["glyph"]}))

    def test_mixed_is_not_variable_only(self):
        self.assertFalse(
            has_only_variable_expectations(
                {
                    "variable.ttf": {"wght=400": ["glyph"]},
                    "static.ttf": ["glyph"],
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
