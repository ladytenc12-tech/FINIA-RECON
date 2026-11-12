
import unittest

from app.business_rules import evaluate_rules


class TestBusinessRules(unittest.TestCase):

    def setUp(self):
        self.internal = [
            {
                "transaction_id": "TX-001",
                "amount": 100,
                "date": "2026-11-11",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-002",
                "amount": 200,
                "date": "2026-11-11",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-003",
                "amount": 300,
                "date": "2026-11-11",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-004",
                "amount": 400,
                "date": "2026-11-11",
                "status": "COMPLETED"
            }
        ]

        self.processor = [
            {
                "transaction_id": "TX-001",
                "amount": 100,
                "date": "2026-11-11",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-002",
                "amount": 250,
                "date": "2026-11-11",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-003",
                "amount": 300,
                "date": "2026-11-12",
                "status": "COMPLETED"
            },
            {
                "transaction_id": "TX-004",
                "amount": 400,
                "date": "2026-11-11",
                "status": "PENDING"
            },
            {
                "transaction_id": "TX-005",
                "amount": 500,
                "date": "2026-11-11",
                "status": "COMPLETED"
            }
        ]

    def test_matching(self):
        results = evaluate_rules(self.internal, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-001")
        self.assertIn("RB01", tx["rule_codes"])

    def test_amount_difference(self):
        results = evaluate_rules(self.internal, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-002")
        self.assertIn("RB02", tx["rule_codes"])

    def test_date_difference(self):
        results = evaluate_rules(self.internal, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-003")
        self.assertIn("RB05", tx["rule_codes"])

    def test_status_difference(self):
        results = evaluate_rules(self.internal, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-004")
        self.assertIn("RB06", tx["rule_codes"])

    def test_missing_transaction(self):
        results = evaluate_rules(self.internal, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-005")
        self.assertIn("RB03", tx["rule_codes"])

    def test_duplicate_transaction(self):
        duplicated = self.processor + [self.processor[0]]
        results = evaluate_rules(self.internal, duplicated)
        tx = next(r for r in results if r["transaction_id"] == "TX-001")
        self.assertIn("RB04", tx["rule_codes"])

    def test_ambiguous_transaction(self):
        duplicated = self.processor + [self.processor[0]]
        results = evaluate_rules(self.internal, duplicated)
        tx = next(r for r in results if r["transaction_id"] == "TX-001")
        self.assertIn("RB07", tx["rule_codes"])

    def test_missing_information(self):
        invalid = self.internal + [{
            "transaction_id": "TX-006",
            "amount": None,
            "date": "2026-11-11",
            "status": "COMPLETED"
        }]
        results = evaluate_rules(invalid, self.processor)
        tx = next(r for r in results if r["transaction_id"] == "TX-006")
        self.assertIn("RB08", tx["rule_codes"])


from app.reconciliation import build_summary


class TestReconciliationSummary(unittest.TestCase):

    def test_summary_counts(self):
        results = [
            {
                "status": "MATCHED",
                "severity": "INFO",
                "rule_codes": ["RB01"]
            },
            {
                "status": "DISCREPANCY",
                "severity": "HIGH",
                "rule_codes": ["RB02"]
            },
            {
                "status": "MISSING",
                "severity": "CRITICAL",
                "rule_codes": ["RB03"]
            }
        ]

        summary = build_summary(results)

        self.assertEqual(summary["total_analyzed"], 3)
        self.assertEqual(summary["matched"], 1)
        self.assertEqual(summary["discrepancies"], 1)
        self.assertEqual(summary["missing"], 1)
        self.assertEqual(summary["pending_review"], 2)
        self.assertEqual(summary["reconciliation_rate"], 33.33)



if __name__ == "__main__":
    unittest.main()