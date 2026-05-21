from .db import all
def load_latest_market_signals():
    rows=all("""SELECT DISTINCT ON (resource_id, signal_type) resource_id, signal_type, value, period, ts
               FROM market_signals ORDER BY resource_id, signal_type, ts DESC""")
    out={}
    for r in rows:
        out.setdefault(r["resource_id"], {})[r["signal_type"]] = float(r["value"])
    return out

def load_supplier_otif_latest():
    rows=all("""SELECT DISTINCT ON (scope_id) scope_id, value, period, ts
               FROM ops_signals WHERE scope_type='supplier' AND metric='otif'
               ORDER BY scope_id, ts DESC""")
    return {r["scope_id"]: float(r["value"]) for r in rows}
