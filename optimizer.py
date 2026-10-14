"""Modelo de planejamento agregado usando programação linear inteira mista."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


FIELDS = ("workers", "hires", "fires", "regular", "overtime_hours", "subcontract", "inventory", "backlog")


@dataclass
class Model:
    months: list[dict[str, Any]]
    params: dict[str, float]

    @property
    def n(self) -> int:
        return len(self.months)

    def ix(self, field: str, month: int) -> int:
        return FIELDS.index(field) * self.n + month


def _number(data: dict[str, Any], name: str, *, minimum: float = 0) -> float:
    try:
        value = float(data[name])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"O campo '{name}' deve ser numérico.") from exc
    if value < minimum:
        raise ValueError(f"O campo '{name}' deve ser maior ou igual a {minimum}.")
    return value


def validate(payload: dict[str, Any]) -> Model:
    months = payload.get("months")
    if not isinstance(months, list) or not months:
        raise ValueError("Informe pelo menos um período no horizonte de planejamento.")
    if len(months) > 60:
        raise ValueError("O horizonte máximo é de 60 períodos.")

    cleaned_months = []
    for pos, month in enumerate(months, 1):
        if not isinstance(month, dict):
            raise ValueError(f"Os dados do período {pos} são inválidos.")
        cleaned_months.append({
            "name": str(month.get("name") or f"Período {pos}")[:40],
            "demand": _number(month, "demand"),
            "days": _number(month, "days", minimum=0.01),
            "subcontract_limit": _number(month, "subcontract_limit"),
        })

    source = payload.get("params") or {}
    names = (
        "initial_workers", "initial_inventory", "initial_backlog", "productive_hours_day",
        "paid_hours_day", "hours_per_unit", "regular_hour_cost", "material_unit_cost",
        "holding_unit_cost", "backlog_unit_cost", "hire_cost", "fire_cost",
        "overtime_hour_cost", "overtime_limit_worker", "overtime_units_hour",
        "subcontract_unit_cost",
    )
    params = {name: _number(source, name) for name in names}
    for required in ("productive_hours_day", "paid_hours_day", "hours_per_unit", "overtime_units_hour"):
        if params[required] <= 0:
            raise ValueError(f"O campo '{required}' deve ser maior que zero.")
    params["initial_workers"] = round(params["initial_workers"])
    params["require_final_service"] = bool(source.get("require_final_service", True))
    return Model(cleaned_months, params)


def optimize(payload: dict[str, Any]) -> dict[str, Any]:
    model = validate(payload)
    n, p = model.n, model.params
    size = len(FIELDS) * n
    c = np.zeros(size)
    lower = np.zeros(size)
    upper = np.full(size, np.inf)
    integrality = np.zeros(size, dtype=int)

    for t, month in enumerate(model.months):
        c[model.ix("workers", t)] = month["days"] * p["paid_hours_day"] * p["regular_hour_cost"]
        c[model.ix("hires", t)] = p["hire_cost"]
        c[model.ix("fires", t)] = p["fire_cost"]
        c[model.ix("regular", t)] = p["material_unit_cost"]
        c[model.ix("overtime_hours", t)] = p["overtime_hour_cost"] + p["material_unit_cost"] * p["overtime_units_hour"]
        c[model.ix("subcontract", t)] = p["subcontract_unit_cost"]
        c[model.ix("inventory", t)] = p["holding_unit_cost"]
        c[model.ix("backlog", t)] = p["backlog_unit_cost"]
        upper[model.ix("subcontract", t)] = month["subcontract_limit"]
        for field in ("workers", "hires", "fires"):
            integrality[model.ix(field, t)] = 1

    rows, lows, highs = [], [], []
    def constraint(terms: dict[int, float], low: float, high: float) -> None:
        row = np.zeros(size)
        for idx, coef in terms.items():
            row[idx] = coef
        rows.append(row); lows.append(low); highs.append(high)

    for t, month in enumerate(model.months):
        # Evolução da força de trabalho.
        workforce = {model.ix("workers", t): 1, model.ix("hires", t): -1, model.ix("fires", t): 1}
        if t:
            workforce[model.ix("workers", t - 1)] = -1
            rhs = 0
        else:
            rhs = p["initial_workers"]
        constraint(workforce, rhs, rhs)

        # Capacidade normal e limite de horas extras.
        regular_capacity = month["days"] * p["productive_hours_day"] / p["hours_per_unit"]
        constraint({model.ix("regular", t): 1, model.ix("workers", t): -regular_capacity}, -np.inf, 0)
        constraint({model.ix("overtime_hours", t): 1, model.ix("workers", t): -p["overtime_limit_worker"]}, -np.inf, 0)

        # Balanço entre produção, estoque e demanda.
        balance = {
            model.ix("regular", t): 1,
            model.ix("overtime_hours", t): p["overtime_units_hour"],
            model.ix("subcontract", t): 1,
            model.ix("inventory", t): -1,
            model.ix("backlog", t): 1,
        }
        if t:
            balance[model.ix("inventory", t - 1)] = 1
            balance[model.ix("backlog", t - 1)] = -1
            rhs = month["demand"]
        else:
            rhs = month["demand"] - p["initial_inventory"] + p["initial_backlog"]
        constraint(balance, rhs, rhs)

    if p["require_final_service"]:
        constraint({model.ix("backlog", n - 1): 1}, 0, 0)

    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(np.asarray(rows), np.asarray(lows), np.asarray(highs)),
        options={"time_limit": 30},
    )
    if not result.success or result.x is None:
        message = "Não foi possível encontrar um plano viável com os limites informados."
        if result.message:
            message += f" Detalhe: {result.message}"
        raise ValueError(message)

    plan, totals = [], {k: 0.0 for k in ("labor", "material", "overtime", "subcontract", "holding", "backlog", "hire", "fire")}
    for t, month in enumerate(model.months):
        values = {field: max(0.0, float(result.x[model.ix(field, t)])) for field in FIELDS}
        overtime_units = values["overtime_hours"] * p["overtime_units_hour"]
        costs = {
            "labor": values["workers"] * month["days"] * p["paid_hours_day"] * p["regular_hour_cost"],
            "material": (values["regular"] + overtime_units) * p["material_unit_cost"],
            "overtime": values["overtime_hours"] * p["overtime_hour_cost"],
            "subcontract": values["subcontract"] * p["subcontract_unit_cost"],
            "holding": values["inventory"] * p["holding_unit_cost"],
            "backlog": values["backlog"] * p["backlog_unit_cost"],
            "hire": values["hires"] * p["hire_cost"],
            "fire": values["fires"] * p["fire_cost"],
        }
        for key, value in costs.items(): totals[key] += value
        plan.append({**month, **values, "overtime_units": overtime_units, "cost": sum(costs.values()), "costs": costs})
    totals["total"] = sum(totals.values())
    return {"success": True, "plan": plan, "costs": totals, "message": "Solução ótima encontrada."}

