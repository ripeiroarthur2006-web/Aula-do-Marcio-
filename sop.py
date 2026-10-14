"""Modelo S&OP/IBP da AgroFlex com capacidades fixas mensais."""

from copy import deepcopy
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DEMAND = [650, 700, 800, 900, 1050, 1200, 1300, 1250, 1100, 900, 750, 700]
FIELDS = ("normal", "overtime", "outsourced", "inventory", "backlog")


def _value(data: dict[str, Any], name: str, default: float, *, positive: bool = False) -> float:
    try:
        value = float(data.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"O campo '{name}' deve ser numérico.") from exc
    if value < 0 or (positive and value <= 0):
        raise ValueError(f"O campo '{name}' deve ser {'maior que zero' if positive else 'não negativo'}.")
    return value


def solve(data: dict[str, Any], demand: list[float], outsource_limits: list[float]) -> dict[str, Any]:
    n = len(MONTHS)
    ix = lambda field, t: FIELDS.index(field) * n + t
    size = len(FIELDS) * n
    normal_cap = _value(data, "normal_capacity", 800)
    overtime_cap = _value(data, "overtime_capacity", 150)
    normal_cost = _value(data, "normal_cost", 500)
    overtime_cost = _value(data, "overtime_cost", 590)
    outsource_cost = _value(data, "outsource_cost", 650)
    holding_cost = _value(data, "holding_cost", 25)
    backlog_cost = _value(data, "backlog_cost", 80)
    initial_inventory = _value(data, "initial_inventory", 250)
    final_inventory = _value(data, "final_inventory", 300)
    stock_limit_value = _value(data, "stock_limit_value", 500000)
    inventory_unit_value = _value(data, "inventory_unit_value", 500, positive=True)
    max_inventory = stock_limit_value / inventory_unit_value

    c = np.zeros(size)
    low = np.zeros(size)
    high = np.full(size, np.inf)
    for t in range(n):
        c[ix("normal", t)] = normal_cost
        c[ix("overtime", t)] = overtime_cost
        c[ix("outsourced", t)] = outsource_cost
        c[ix("inventory", t)] = holding_cost
        c[ix("backlog", t)] = backlog_cost
        high[ix("normal", t)] = normal_cap
        high[ix("overtime", t)] = overtime_cap
        high[ix("outsourced", t)] = outsource_limits[t]
        high[ix("inventory", t)] = max_inventory

    rows, lower, upper = [], [], []
    for t in range(n):
        row = np.zeros(size)
        row[ix("normal", t)] = row[ix("overtime", t)] = row[ix("outsourced", t)] = 1
        row[ix("inventory", t)] = -1
        row[ix("backlog", t)] = 1
        if t:
            row[ix("inventory", t - 1)] = 1
            row[ix("backlog", t - 1)] = -1
            rhs = demand[t]
        else:
            rhs = demand[t] - initial_inventory
        rows.append(row); lower.append(rhs); upper.append(rhs)
    row = np.zeros(size); row[ix("inventory", n - 1)] = 1
    rows.append(row); lower.append(final_inventory); upper.append(np.inf)
    row = np.zeros(size); row[ix("backlog", n - 1)] = 1
    rows.append(row); lower.append(0); upper.append(0)

    result = milp(c=c, bounds=Bounds(low, high), constraints=LinearConstraint(np.asarray(rows), lower, upper))
    if not result.success or result.x is None:
        raise ValueError("Não existe plano viável com as capacidades e limites informados.")
    plan, costs = [], {"normal": 0.0, "overtime": 0.0, "outsourced": 0.0, "inventory": 0.0, "backlog": 0.0}
    for t, month in enumerate(MONTHS):
        values = {field: max(0.0, float(result.x[ix(field, t)])) for field in FIELDS}
        monthly_costs = {
            "normal": values["normal"] * normal_cost,
            "overtime": values["overtime"] * overtime_cost,
            "outsourced": values["outsourced"] * outsource_cost,
            "inventory": values["inventory"] * holding_cost,
            "backlog": values["backlog"] * backlog_cost,
        }
        for key in costs: costs[key] += monthly_costs[key]
        plan.append({"name": month, "demand": demand[t], **values,
                     "normal_use": values["normal"] / normal_cap * 100 if normal_cap else 0,
                     "cost": sum(monthly_costs.values())})
    costs["total"] = sum(costs.values())
    return {"plan": plan, "costs": costs, "max_inventory_units": max_inventory}


def compare_sop_scenarios(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    price = _value(options, "sale_price", 900)
    campaign_cost = _value(options, "campaign_cost", 150000)
    increase = _value(options, "campaign_increase", 10) / 100
    outsource_cap = _value(options, "outsource_capacity", 200)
    scenarios = []
    for name, marketing, risk in (("Base", False, False), ("Marketing", True, False), ("Risco", False, True), ("Combinado", True, True)):
        demand = [float(x) for x in DEMAND]
        if marketing:
            for t in range(4, 8): demand[t] *= 1 + increase
        limits = [outsource_cap] * 12
        if risk:
            limits[6] *= .5; limits[7] *= .5
        result = solve(options, demand, limits)
        for month in result["plan"]:
            month["revenue"] = month["demand"] * price
        total_demand = sum(demand)
        revenue = total_demand * price
        campaign = campaign_cost if marketing else 0
        economic = revenue - result["costs"]["total"] - campaign
        scenarios.append({"name": name, "marketing": marketing, "risk": risk,
                          "demand": total_demand, "revenue": revenue, "campaign_cost": campaign,
                          "economic_result": economic,
                          "max_inventory": max(x["inventory"] for x in result["plan"]),
                          "max_backlog": max(x["backlog"] for x in result["plan"]),
                          "normal_utilization": sum(x["normal"] for x in result["plan"]) / (12 * _value(options, "normal_capacity", 800)) * 100,
                          **result})
    recommended = max(scenarios, key=lambda x: x["economic_result"])["name"]
    return {"success": True, "scenarios": scenarios, "recommended": recommended,
            "assumption": "O valor unitário do estoque é editável e foi usado para converter o limite financeiro em unidades."}

