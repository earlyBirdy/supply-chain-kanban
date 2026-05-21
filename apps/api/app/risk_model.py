def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))
def compute_risk(resource_signals: dict, supplier_otif: dict):
    price = resource_signals.get("price_index", 1.0)
    market = 90 if price>=1.30 else 70 if price>=1.20 else 50 if price>=1.10 else 30
    if supplier_otif:
        worst=min(supplier_otif.values())
        supply = 80 if worst<0.90 else 60 if worst<0.95 else 30
    else:
        worst = None
        supply = 40
    risk=int(round(0.55*market+0.45*supply))
    conf=0.75 if risk>=70 else 0.6
    ltf=21 if risk>=85 else 45 if risk>=70 else 90
    return clamp(risk), conf, ltf, {"price_index":price,"worst_supplier_otif":worst}
