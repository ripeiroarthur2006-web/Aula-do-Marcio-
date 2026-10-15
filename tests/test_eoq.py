import unittest

from eoq import calculate_eoq


class EoqTest(unittest.TestCase):
    def test_classic_eoq_and_reorder_point(self):
        result = calculate_eoq({
            "selected_costs": [1, 2, 4], "annual_demand": 10000,
            "unit_price": 25, "order_cost": 120, "capital_rate": 20,
            "working_days": 250, "lead_time_days": 5,
            "daily_demand_sigma": 0, "service_level": 95,
            "minimum_lot": 1, "lot_multiple": 1, "maximum_lot": 5000,
            "item_type": "Compra",
        })
        self.assertAlmostEqual(result["economic_lot"], 693, delta=1)
        self.assertAlmostEqual(result["reorder_point"], 200)
        self.assertTrue(result["minimum_confirmed"])

    def test_safety_stock_increases_with_service(self):
        base = {"selected_costs": [2, 5], "annual_demand": 1000,
                "order_cost": 100, "storage_unit_year": 10, "working_days": 250,
                "lead_time_days": 9, "daily_demand_sigma": 2,
                "minimum_lot": 1, "lot_multiple": 1, "maximum_lot": 1000,
                "item_type": "Compra"}
        low = calculate_eoq({**base, "service_level": 90})
        high = calculate_eoq({**base, "service_level": 99})
        self.assertGreater(high["safety_stock"], low["safety_stock"])


if __name__ == "__main__":
    unittest.main()
