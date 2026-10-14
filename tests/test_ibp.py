import unittest

from ibp import compare_scenarios


class IbpTest(unittest.TestCase):
    def test_all_scenarios_respect_case_limits(self):
        result = compare_scenarios({})
        self.assertEqual(len(result["scenarios"]), 4)
        for scenario in result["scenarios"]:
            self.assertLessEqual(scenario["max_inventory"], 625.0001)
            self.assertLessEqual(max(x["workers"] for x in scenario["plan"]), 22.0001)
            self.assertAlmostEqual(scenario["plan"][-1]["backlog"], 0)
            self.assertGreaterEqual(scenario["plan"][-1]["inventory"], 249.9999)


if __name__ == "__main__":
    unittest.main()

