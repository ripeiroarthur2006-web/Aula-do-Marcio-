"""Comparação dos quatro cenários didáticos de IBP da AgroFlex."""

from copy import deepcopy

from optimizer import optimize


DEMAND = [650, 700, 800, 900, 1050, 1200, 1300, 1250, 1100, 900, 750, 700]
MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def base_payload() -> dict:
    return {
        "params": {
            "initial_workers": 18, "initial_inventory": 250, "initial_backlog": 0,
            "productive_hours_day": 7, "paid_hours_day": 8, "hours_per_unit": 3.5,
            "regular_hour_cost": 17.5, "material_unit_cost": 250,
            "holding_unit_cost": 20, "backlog_unit_cost": 80,
            "hire_cost": 2500, "fire_cost": 6000,
            "overtime_hour_cost": 30, "overtime_limit_worker": 30,
            "overtime_units_hour": 0.9 / 3.5, "subcontract_unit_cost": 390,
            "require_final_service": True, "max_workers": 22,
            "max_inventory": 625, "min_final_inventory": 250,
        },
        "months": [
            {"name": name, "demand": demand, "days": 22, "subcontract_limit": 200}
            for name, demand in zip(MONTHS, DEMAND)
        ],
    }


def compare_scenarios(options: dict | None = None) -> dict:
    options = options or {}
    price = float(options.get("sale_price", 650))
    campaign_cost = float(options.get("campaign_cost", 90000))
    campaign_increase = float(options.get("campaign_increase", 10)) / 100
    scenarios = []
    definitions = [
        ("Base", False, False), ("Comercial", True, False),
        ("Risco", False, True), ("Combinado", True, True),
    ]
    for name, commercial, risk in definitions:
        data = deepcopy(base_payload())
        if commercial:
            for t in range(4, 8):
                data["months"][t]["demand"] *= 1 + campaign_increase
        if risk:
            data["months"][6]["subcontract_limit"] = 100
            data["months"][7]["subcontract_limit"] = 100
        result = optimize(data)
        demand = sum(m["demand"] for m in data["months"])
        campaign = campaign_cost if commercial else 0
        revenue = demand * price
        economic_result = revenue - result["costs"]["total"] - campaign
        scenarios.append({
            "name": name, "commercial": commercial, "risk": risk,
            "demand": demand, "revenue": revenue, "campaign_cost": campaign,
            "economic_result": economic_result,
            "max_inventory": max(x["inventory"] for x in result["plan"]),
            "max_backlog": max(x["backlog"] for x in result["plan"]),
            "total_hires": sum(x["hires"] for x in result["plan"]),
            "total_overtime": sum(x["overtime_hours"] for x in result["plan"]),
            "total_subcontract": sum(x["subcontract"] for x in result["plan"]),
            **result,
        })
    best = max(scenarios, key=lambda x: x["economic_result"])
    return {"success": True, "scenarios": scenarios, "recommended": best["name"]}

