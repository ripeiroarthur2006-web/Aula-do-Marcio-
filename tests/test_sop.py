import unittest

from sop import compare_sop_scenarios


class SopTest(unittest.TestCase):
    def test_scenarios_respect_capacity_and_closing_stock(self):
        result = compare_sop_scenarios({})
        self.assertEqual(len(result["scenarios"]), 4)
        for scenario in result["scenarios"]:
            self.assertLessEqual(scenario["max_inventory"], 1000.0001)
            self.assertAlmostEqual(scenario["plan"][-1]["backlog"], 0)
            self.assertGreaterEqual(scenario["plan"][-1]["inventory"], 299.9999)
            self.assertLessEqual(max(x["normal"] for x in scenario["plan"]), 800.0001)


if __name__ == "__main__":
    unittest.main()
