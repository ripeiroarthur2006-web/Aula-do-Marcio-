"""Lote econômico, estoque de segurança e ponto de pedido."""

from math import ceil, floor, isfinite, sqrt
from statistics import NormalDist
from typing import Any


def _n(data: dict[str, Any], name: str, default: float = 0, *, positive: bool = False) -> float:
    try:
        value = float(data.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"O campo '{name}' deve ser numérico.") from exc
    if value < 0 or (positive and value <= 0):
        raise ValueError(f"O campo '{name}' deve ser {'maior que zero' if positive else 'não negativo'}.")
    return value


def calculate_eoq(data: dict[str, Any]) -> dict[str, Any]:
    selected = {int(x) for x in data.get("selected_costs", [])}
    demand = _n(data, "annual_demand", positive=True)
    base_price = _n(data, "unit_price")
    working_days = _n(data, "working_days", 250, positive=True)
    lead_days = _n(data, "lead_time_days")
    daily_sigma = _n(data, "daily_demand_sigma")
    service = _n(data, "service_level", 95)
    if not 50 < service < 100:
        raise ValueError("O nível de serviço deve estar entre 50% e 100%.")
    z = NormalDist().inv_cdf(service / 100)
    safety_stock = z * daily_sigma * sqrt(lead_days)
    reorder_point = demand / working_days * lead_days + safety_stock

    order_cost = (_n(data, "order_cost") if 2 in selected else 0) + (_n(data, "setup_cost") if 3 in selected else 0)
    order_cost += (_n(data, "freight_per_shipment") if 16 in selected else 0) + (_n(data, "receiving_cost") if 17 in selected else 0)
    rates = sum(_n(data, key) for number, key in ((4,"capital_rate"),(6,"insurance_rate"),(7,"tax_rate"),(8,"obsolescence_rate"),(9,"deterioration_rate"),(10,"loss_rate")) if number in selected) / 100
    storage = _n(data, "storage_unit_year") if 5 in selected else 0
    item_type = str(data.get("item_type", "Compra"))
    production_rate = _n(data, "production_rate")
    production_factor = 1.0
    if item_type == "Fabricação":
        if production_rate <= demand:
            raise ValueError("Na fabricação, a taxa anual de produção deve ser maior que a demanda anual.")
        production_factor = 1 - demand / production_rate

    discount_threshold = _n(data, "discount_threshold") if 18 in selected else 0
    discount_price = _n(data, "discount_price") if 18 in selected else base_price
    min_lot = max(_n(data, "minimum_lot"), 0.000001)
    multiple = _n(data, "lot_multiple", 1, positive=True)
    max_lot = _n(data, "maximum_lot") or float("inf")
    if max_lot < min_lot:
        raise ValueError("O lote máximo deve ser maior ou igual ao lote mínimo.")

    def price(q: float) -> float:
        return discount_price if discount_threshold and q >= discount_threshold else base_price

    def holding(q: float) -> float:
        return storage + price(q) * rates

    fixed_annual = 0.0
    if 11 in selected: fixed_annual += _n(data, "annual_movements") * _n(data, "movement_cost")
    if 12 in selected: fixed_annual += _n(data, "expected_shortages") * _n(data, "shortage_unit_cost")
    if 13 in selected: fixed_annual += _n(data, "lost_sales_units") * _n(data, "lost_margin")
    if 14 in selected: fixed_annual += _n(data, "backorder_units") * _n(data, "backorder_unit_cost")
    if 15 in selected: fixed_annual += _n(data, "penalty_events") * _n(data, "penalty_cost")

    def components(q: float) -> dict[str, float]:
        avg = q / 2 * production_factor + safety_stock
        purchase = demand * price(q) if 1 in selected or 18 in selected else 0
        replenishment = demand / q * order_cost
        capital = avg * price(q) * rates
        physical = avg * storage
        return {"Aquisição": purchase, "Reposição": replenishment,
                "Manutenção por taxas": capital, "Armazenagem física": physical,
                "Ruptura e movimentação": fixed_annual}

    def total(q: float) -> float:
        return sum(components(q).values())

    candidates = {min_lot, max_lot if isfinite(max_lot) else min_lot}
    for candidate_price, lower in ((base_price, min_lot), (discount_price, discount_threshold)):
        h = storage + candidate_price * rates
        if order_cost > 0 and h > 0 and production_factor > 0:
            raw = sqrt(2 * demand * order_cost / (h * production_factor))
            for value in (raw, floor(raw / multiple) * multiple, ceil(raw / multiple) * multiple):
                if value > 0: candidates.add(value)
        if lower: candidates.update((lower, max(min_lot, lower - multiple)))
    feasible = []
    for q in candidates:
        q = max(min_lot, ceil(q / multiple - 1e-12) * multiple)
        if q <= max_lot: feasible.append(q)
    if not feasible:
        raise ValueError("Nenhum lote atende às restrições informadas.")
    optimum = min(set(feasible), key=total)
    h_opt = holding(optimum)
    second_derivative = 2 * demand * order_cost / optimum**3 if order_cost else 0
    details = components(optimum)
    curve = []
    low = max(min_lot, optimum * .25); high = min(max_lot, optimum * 2.25)
    if not isfinite(high): high = optimum * 2.25
    for i in range(31):
        q = low + (high - low) * i / 30
        q = max(min_lot, ceil(q / multiple - 1e-12) * multiple)
        if not curve or q != curve[-1]["quantity"]:
            parts = components(q)
            maintenance = parts["Manutenção por taxas"] + parts["Armazenagem física"]
            curve.append({"quantity": q, "total_cost": total(q),
                          "replenishment_cost": parts["Reposição"],
                          "maintenance_cost": maintenance,
                          "relevant_cost": parts["Reposição"] + maintenance})
    return {"success": True, "economic_lot": optimum, "reorder_point": reorder_point,
            "safety_stock": safety_stock, "z_factor": z, "orders_per_year": demand / optimum,
            "cycle_days": working_days * optimum / demand, "annual_total_cost": total(optimum),
            "holding_cost_unit_year": h_opt, "second_derivative": second_derivative,
            "minimum_confirmed": second_derivative > 0, "costs": details, "curve": curve,
            "assumption": "Custos de ruptura e movimentação informados como totais anuais afetam o custo total, mas não deslocam o lote econômico no modelo básico."}

