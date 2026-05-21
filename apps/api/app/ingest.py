import os
import pandas as pd
from .config import INGEST_DIR
from .db import q

def _read_csv(path: str):
    return pd.read_csv(path) if os.path.exists(path) else None

def ingest_erp():
    df = _read_csv(os.path.join(INGEST_DIR, "erp", "orders.csv"))
    if df is None or df.empty:
        return 0
    n=0
    for _, r in df.iterrows():
        d={k:(None if pd.isna(v) else v) for k,v in r.to_dict().items()}
        q("""
        INSERT INTO erp_orders(order_id, sku, location, qty, need_date, net_price)
        VALUES (:order_id, :sku, :location, :qty, :need_date, :net_price)
        ON CONFLICT (order_id) DO UPDATE
        SET sku=EXCLUDED.sku, location=EXCLUDED.location, qty=EXCLUDED.qty,
            need_date=EXCLUDED.need_date, net_price=EXCLUDED.net_price, ts=now()
        """, **d)
        n+=1
    return n

def ingest_wms():
    df = _read_csv(os.path.join(INGEST_DIR, "wms", "shipments.csv"))
    if df is None or df.empty:
        return 0
    n=0
    for _, r in df.iterrows():
        d={k:(None if pd.isna(v) else v) for k,v in r.to_dict().items()}
        if isinstance(d.get("delivered_on_time"), str):
            d["delivered_on_time"] = d["delivered_on_time"].strip().lower() in ("true","1","yes")
        q("""
        INSERT INTO wms_shipments(shipment_id, order_id, supplier_id, delivered_qty, ordered_qty, delivered_on_time, lead_time_days, period)
        VALUES (:shipment_id, :order_id, :supplier_id, :delivered_qty, :ordered_qty, :delivered_on_time, :lead_time_days, :period)
        ON CONFLICT (shipment_id) DO UPDATE
        SET order_id=EXCLUDED.order_id, supplier_id=EXCLUDED.supplier_id,
            delivered_qty=EXCLUDED.delivered_qty, ordered_qty=EXCLUDED.ordered_qty,
            delivered_on_time=EXCLUDED.delivered_on_time, lead_time_days=EXCLUDED.lead_time_days,
            period=EXCLUDED.period, ts=now()
        """, **d)
        n+=1
    return n

def ingest_mes():
    df = _read_csv(os.path.join(INGEST_DIR, "mes", "production.csv"))
    if df is None or df.empty:
        return 0
    n=0
    for _, r in df.iterrows():
        d={k:(None if pd.isna(v) else v) for k,v in r.to_dict().items()}
        q("""
        INSERT INTO mes_production(record_id, plant_id, sku, input_qty, good_qty, scrap_qty, period)
        VALUES (:record_id, :plant_id, :sku, :input_qty, :good_qty, :scrap_qty, :period)
        ON CONFLICT (record_id) DO UPDATE
        SET plant_id=EXCLUDED.plant_id, sku=EXCLUDED.sku, input_qty=EXCLUDED.input_qty,
            good_qty=EXCLUDED.good_qty, scrap_qty=EXCLUDED.scrap_qty, period=EXCLUDED.period, ts=now()
        """, **d)
        n+=1
    return n

def run_all():
    return {"erp": ingest_erp(), "wms": ingest_wms(), "mes": ingest_mes()}
