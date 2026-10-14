import unittest

from optimizer import optimize


class OptimizerTest(unittest.TestCase):
    def test_simple_plan_uses_one_worker(self):
        data = {"params": {
            "initial_workers": 1, "initial_inventory": 0, "initial_backlog": 0,
            "productive_hours_day": 8, "paid_hours_day": 8, "hours_per_unit": 1,
            "regular_hour_cost": 10, "material_unit_cost": 2, "holding_unit_cost": 1,
            "backlog_unit_cost": 100, "hire_cost": 500, "fire_cost": 500,
            "overtime_hour_cost": 20, "overtime_limit_worker": 0,
            "overtime_units_hour": 1, "subcontract_unit_cost": 100,
            "require_final_service": True,
        }, "months": [{"name": "M1", "demand": 80, "days": 10, "subcontract_limit": 0}]}
        result = optimize(data)
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["plan"][0]["workers"], 1)
        self.assertAlmostEqual(result["plan"][0]["regular"], 80)
        self.assertAlmostEqual(result["plan"][0]["backlog"], 0)

    def test_overtime_respects_limit(self):
        data = {"params": {
            "initial_workers": 1, "initial_inventory": 0, "initial_backlog": 0,
            "productive_hours_day": 8, "paid_hours_day": 8, "hours_per_unit": 1,
            "regular_hour_cost": 10, "material_unit_cost": 0, "holding_unit_cost": 1,
            "backlog_unit_cost": 1000, "hire_cost": 10000, "fire_cost": 500,
            "overtime_hour_cost": 5, "overtime_limit_worker": 10,
            "overtime_units_hour": 2, "subcontract_unit_cost": 100,
            "require_final_service": True,
        }, "months": [{"name": "M1", "demand": 100, "days": 10, "subcontract_limit": 100}]}
        result = optimize(data)
        self.assertAlmostEqual(result["plan"][0]["overtime_hours"], 10)
        self.assertAlmostEqual(result["plan"][0]["overtime_units"], 20)


if __name__ == "__main__":
    unittest.main()

