"""Explosão MRP multinível com estoque de segurança e políticas de lote."""

from __future__ import annotations
from math import ceil
from typing import Any


def _item(code, name, origin, lead, stock, safety, policy, lot, unit="un"):
    return {"code": code, "name": name, "origin": origin, "lead_time": lead,
            "initial_stock": stock, "safety_stock": safety, "lot_policy": policy,
            "lot_size": lot, "unit": unit}


def default_catalog() -> dict[str, Any]:
    cup_items = [
        _item("COP-STN-887","Copo térmico tipo Stanley 887 ml","Fabricado",1,40,20,"Lote econômico",200),
        _item("CJT-CORPO","Conjunto corpo térmico","Fabricado",2,20,10,"Múltiplo fixo",100),
        _item("CAS-EXT-304","Casco externo em inox 304","Comprado",3,100,50,"Lote econômico",500),
        _item("CAS-INT-304","Casco interno em inox 304","Comprado",3,100,50,"Lote econômico",500),
        _item("DSC-BASE-304","Disco de base em inox","Comprado",2,150,50,"Múltiplo fixo",250),
        _item("TINTA-PO-PT","Tinta em pó preta","Comprado",2,10,5,"Lote econômico",25,"kg"),
        _item("ANEL-BASE-SIL","Anel antiderrapante de silicone","Comprado",2,200,100,"Lote econômico",500),
        _item("CJT-TAMPA","Conjunto tampa","Fabricado",1,50,25,"Múltiplo fixo",100),
        _item("TAMPA-TRITAN","Corpo da tampa em Tritan","Comprado",3,120,50,"Lote econômico",500),
        _item("VED-TAMPA-SIL","Vedação da tampa em silicone","Comprado",2,200,100,"Lote econômico",500),
        _item("DESL-TAMPA-PP","Deslizador da tampa em PP","Comprado",2,150,50,"Múltiplo fixo",250),
        _item("CJT-ALCA","Conjunto alça","Fabricado",1,40,20,"Múltiplo fixo",100),
        _item("ALCA-PP","Alça em polipropileno","Comprado",3,100,50,"Lote econômico",500),
        _item("PINO-ALCA-INOX","Pino de fixação da alça","Comprado",2,300,100,"Lote econômico",1000),
        _item("CANUDO-PLAST","Canudo plástico reutilizável","Comprado",2,300,100,"Lote econômico",1000),
        _item("CJT-EMB-COP","Kit de embalagem do copo","Fabricado",1,30,20,"Lote a lote",1,"kit"),
        _item("CX-KRAFT-COP","Caixa kraft individual","Comprado",2,200,100,"Lote econômico",500),
        _item("MAN-CUID-COP","Manual de uso e cuidados","Comprado",1,500,200,"Lote econômico",1000),
    ]
    cup_bom = [("COP-STN-887",c,q) for c,q in [("CJT-CORPO",1),("CJT-TAMPA",1),("CJT-ALCA",1),("CANUDO-PLAST",1),("CJT-EMB-COP",1)]] + [
        ("CJT-CORPO","CAS-EXT-304",1),("CJT-CORPO","CAS-INT-304",1),("CJT-CORPO","DSC-BASE-304",1),("CJT-CORPO","TINTA-PO-PT",.025),("CJT-CORPO","ANEL-BASE-SIL",1),
        ("CJT-TAMPA","TAMPA-TRITAN",1),("CJT-TAMPA","VED-TAMPA-SIL",1),("CJT-TAMPA","DESL-TAMPA-PP",1),
        ("CJT-ALCA","ALCA-PP",1),("CJT-ALCA","PINO-ALCA-INOX",2),("CJT-EMB-COP","CX-KRAFT-COP",1),("CJT-EMB-COP","MAN-CUID-COP",1)]
    glasses_items = [
        _item("OCL-MET-01","Óculos de grau — armação metálica","Fabricado",1,25,10,"Lote econômico",100),
        _item("CJT-ARM-MET","Conjunto armação metálica","Fabricado",2,20,10,"Múltiplo fixo",50),
        _item("FRT-ARM-MET","Frontal metálico","Fabricado",1,30,10,"Múltiplo fixo",50),
        _item("FIO-INOX-OC","Fio de aço inoxidável","Comprado",3,8,3,"Lote econômico",20,"kg"),
        _item("SOLDA-PRATA","Liga de solda prata","Comprado",2,.5,.2,"Múltiplo fixo",1,"kg"),
        _item("HASTE-D-MET","Haste direita metálica","Fabricado",1,30,10,"Múltiplo fixo",50),
        _item("VARETA-D-INOX","Vareta inox para haste direita","Comprado",2,40,15,"Lote econômico",100,"m"),
        _item("PONT-D-ACET","Ponteira direita em acetato","Comprado",2,100,50,"Lote econômico",500),
        _item("HASTE-E-MET","Haste esquerda metálica","Fabricado",1,30,10,"Múltiplo fixo",50),
        _item("VARETA-E-INOX","Vareta inox para haste esquerda","Comprado",2,40,15,"Lote econômico",100,"m"),
        _item("PONT-E-ACET","Ponteira esquerda em acetato","Comprado",2,100,50,"Lote econômico",500),
        _item("DOBR-MINI","Dobradiça miniatura","Comprado",3,300,100,"Lote econômico",1000),
        _item("PARAF-MINI","Parafuso para dobradiça","Comprado",2,400,200,"Lote econômico",2000),
        _item("PLAQ-NASAL-SIL","Plaqueta nasal em silicone","Comprado",2,300,100,"Lote econômico",1000),
        _item("LENTE-OD-BASE","Lente base — olho direito","Comprado",2,80,30,"Lote a lote",1),
        _item("LENTE-OE-BASE","Lente base — olho esquerdo","Comprado",2,80,30,"Lote a lote",1),
        _item("ESTOJO-OC","Estojo rígido para óculos","Comprado",2,120,50,"Lote econômico",500),
        _item("PANO-MICROF","Pano de microfibra","Comprado",1,200,100,"Lote econômico",1000),
        _item("CJT-EMB-OC","Kit de embalagem dos óculos","Fabricado",1,20,10,"Lote a lote",1,"kit"),
        _item("CX-KRAFT-OC","Caixa externa para óculos","Comprado",2,150,50,"Lote econômico",500),
        _item("CERT-GAR-OC","Certificado e manual","Comprado",1,300,100,"Lote econômico",1000),
    ]
    glasses_bom = [("OCL-MET-01",c,q) for c,q in [("CJT-ARM-MET",1),("LENTE-OD-BASE",1),("LENTE-OE-BASE",1),("ESTOJO-OC",1),("PANO-MICROF",1),("CJT-EMB-OC",1)]] + [
        ("CJT-ARM-MET","FRT-ARM-MET",1),("CJT-ARM-MET","HASTE-D-MET",1),("CJT-ARM-MET","HASTE-E-MET",1),("CJT-ARM-MET","DOBR-MINI",2),("CJT-ARM-MET","PARAF-MINI",2),("CJT-ARM-MET","PLAQ-NASAL-SIL",2),
        ("FRT-ARM-MET","FIO-INOX-OC",.08),("FRT-ARM-MET","SOLDA-PRATA",.002),("HASTE-D-MET","VARETA-D-INOX",.14),("HASTE-D-MET","PONT-D-ACET",1),("HASTE-E-MET","VARETA-E-INOX",.14),("HASTE-E-MET","PONT-E-ACET",1),("CJT-EMB-OC","CX-KRAFT-OC",1),("CJT-EMB-OC","CERT-GAR-OC",1)]
    def product(name, root, items, bom):
        return {"name": name, "root": root, "items": items,
                "bom": [{"parent": p, "child": c, "quantity": q} for p,c,q in bom]}
    return {"products": [product("Copo térmico 887 ml","COP-STN-887",cup_items,cup_bom), product("Óculos de grau metálico","OCL-MET-01",glasses_items,glasses_bom)]}


def calculate_mrp(payload: dict[str, Any]) -> dict[str, Any]:
    product = payload.get("product") or {}
    items_list, bom = product.get("items"), product.get("bom")
    root = str(product.get("root", "")).strip()
    if not isinstance(items_list, list) or not items_list or not root:
        raise ValueError("Cadastre um produto, seus itens e o código raiz.")
    items = {str(x.get("code", "")).strip(): x for x in items_list}
    if "" in items or root not in items or len(items) != len(items_list):
        raise ValueError("Os códigos dos itens devem ser únicos e o item raiz deve existir.")
    children = {code: [] for code in items}
    parents = {code: [] for code in items}
    for link in bom or []:
        p, c = str(link.get("parent", "")), str(link.get("child", ""))
        if p not in items or c not in items or p == c: raise ValueError("A estrutura contém um vínculo inválido.")
        try: qty = float(link.get("quantity", 0))
        except (TypeError, ValueError): raise ValueError("As quantidades da estrutura devem ser numéricas.")
        if qty <= 0: raise ValueError("As quantidades da estrutura devem ser positivas.")
        children[p].append((c, qty)); parents[c].append(p)
    # Ordenação topológica e detecção de ciclos.
    degree = {c: len(parents[c]) for c in items}; queue = [c for c,d in degree.items() if d == 0]; order = []
    while queue:
        code = queue.pop(0); order.append(code)
        for child,_ in children[code]:
            degree[child] -= 1
            if degree[child] == 0: queue.append(child)
    if len(order) != len(items): raise ValueError("A árvore contém um ciclo entre componentes.")
    if any(code != root and not parents[code] for code in items): raise ValueError("Existem itens desconectados do produto raiz.")
    horizon = int(payload.get("horizon", 12)); due = int(payload.get("due_week", 8)); quantity = float(payload.get("quantity", 0))
    if not 1 <= horizon <= 104 or not 1 <= due <= horizon or quantity <= 0: raise ValueError("Revise horizonte, semana de entrega e quantidade do pedido.")
    gross = {c: [0.0] * (horizon + 1) for c in items}; gross[root][due] = quantity
    records, actions = {}, []
    for code in order:
        x = items[code]
        try:
            lead=int(x.get("lead_time",0)); stock=float(x.get("initial_stock",0)); safety=float(x.get("safety_stock",0)); lot=float(x.get("lot_size",1))
        except (TypeError,ValueError): raise ValueError(f"Parâmetros inválidos no item {code}.")
        if lead < 0 or stock < 0 or safety < 0 or lot <= 0: raise ValueError(f"Parâmetros negativos ou lote inválido no item {code}.")
        projected=[0.0]*(horizon+1); net=[0.0]*(horizon+1); receipts=[0.0]*(horizon+1); releases=[0.0]*(horizon+1); projected[0]=stock
        urgent=0.0
        for week in range(1,horizon+1):
            available=projected[week-1]-gross[code][week]
            if available < safety:
                net[week]=safety-available
                policy=str(x.get("lot_policy","Lote a lote"))
                receipt=net[week] if policy == "Lote a lote" else ceil(net[week]/lot-1e-12)*lot
                receipts[week]=receipt; available+=receipt
                release_week=week-lead
                if release_week < 1: urgent+=receipt
                else: releases[release_week]+=receipt
            projected[week]=available
        if urgent: actions.append({"week":0,"code":code,"name":x.get("name",code),"origin":x.get("origin","Comprado"),"quantity":urgent,"unit":x.get("unit","un"),"late":True})
        for week in range(1,horizon+1):
            if releases[week]: actions.append({"week":week,"code":code,"name":x.get("name",code),"origin":x.get("origin","Comprado"),"quantity":releases[week],"unit":x.get("unit","un"),"late":False})
            for child,qty in children[code]: gross[child][week]+=releases[week]*qty
        records[code]={"item":x,"gross":gross[code],"projected":projected,"net":net,"receipts":receipts,"releases":releases}
    actions.sort(key=lambda a:(a["week"],a["origin"],a["code"]))
    return {"success":True,"records":records,"actions":actions,"order":order,"horizon":horizon}

