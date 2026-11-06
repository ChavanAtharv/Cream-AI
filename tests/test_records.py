"""Unit tests for SchemeSaathi record functions."""

import unittest

from app.records import count_by, get_by_id, load_records, search


class TestRecords(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"id": "A1", "scheme_name": "Atal Pension Yojana",
             "category": "Pension", "benefit": "Monthly pension"},
            {"id": "B1", "scheme_name": "PM-KISAN",
             "category": "Agriculture", "benefit": "Farmer income support"},
        ]

    def test_loads_twenty_default_records(self):
        records = load_records()
        self.assertEqual(len(records), 20)
        self.assertEqual(len({item["id"] for item in records}), 20)

    def test_load_custom_records(self):
        self.assertEqual(load_records(self.records), self.records)

    def test_search_existing_keyword(self):
        self.assertEqual(len(search(self.records, "pension")), 1)

    def test_search_is_case_insensitive(self):
        self.assertEqual(len(search(self.records, "PM-KISAN")), 1)
        self.assertEqual(len(search(self.records, "pm-kisan")), 1)

    def test_search_across_fields(self):
        self.assertEqual(len(search(self.records, "income support")), 1)

    def test_search_no_match_and_blank(self):
        self.assertEqual(search(self.records, "not-a-scheme"), [])
        self.assertEqual(search(self.records, "   "), [])

    def test_search_rejects_non_string(self):
        with self.assertRaises(TypeError):
            search(self.records, 42)

    def test_count_by_category(self):
        self.assertEqual(count_by(self.records)["Pension"], 1)
        self.assertEqual(count_by(self.records)["Agriculture"], 1)

    def test_get_by_id(self):
        self.assertEqual(get_by_id(self.records, "a1")["scheme_name"],
                         "Atal Pension Yojana")
        self.assertIsNone(get_by_id(self.records, "missing"))

    def test_invalid_count_field(self):
        with self.assertRaises(ValueError):
            count_by(self.records, "")


if __name__ == "__main__":
    unittest.main()
