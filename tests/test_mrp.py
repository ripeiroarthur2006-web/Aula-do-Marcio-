import unittest

from mrp import calculate_mrp, default_catalog


class MrpTest(unittest.TestCase):
    def test_cup_order_explodes_components_and_creates_actions(self):
        product = default_catalog()["products"][0]
        result = calculate_mrp({"product": product, "horizon": 12, "due_week": 8, "quantity": 500})
        self.assertTrue(result["success"])
        self.assertGreater(sum(result["records"]["CJT-CORPO"]["gross"]), 0)
        self.assertTrue(any(a["origin"] == "Comprado" for a in result["actions"]))
        self.assertTrue(any(a["origin"] == "Fabricado" for a in result["actions"]))

    def test_cycle_is_rejected(self):
        product = default_catalog()["products"][0]
        product["bom"].append({"parent": "CJT-CORPO", "child": "COP-STN-887", "quantity": 1})
        with self.assertRaisesRegex(ValueError, "ciclo"):
            calculate_mrp({"product": product, "horizon": 12, "due_week": 8, "quantity": 500})


if __name__ == "__main__":
    unittest.main()
