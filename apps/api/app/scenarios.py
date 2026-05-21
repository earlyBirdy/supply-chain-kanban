import json
from .db import q, one

def compute_baseline():
    r=one("""SELECT COALESCE(SUM(qty),0) AS demand_qty, COALESCE(AVG(net_price),0) AS price FROM erp_orders""")
    demand=float(r["demand_qty"]) if r else 0.0
    price=float(r["price"]) if r else 0.0
    s=one("""SELECT COALESCE(SUM(delivered_qty),0) AS supply_qty FROM wms_shipments""")
    supply=float(s["supply_qty"]) if s else 0.0
    return demand,supply,price

def persist_scenarios(case_id: str, risk_score: int):
    demand,supply,price=compute_baseline()
    q("""DELETE FROM agent_scenarios WHERE case_id=:cid""", cid=case_id)
    scenarios=[
      ("Base",1.00,1.00,1.00),
      ("SupplyShock",0.80,1.00,1.00),
      ("PriceShock",1.00,1.30,1.00),
      ("DoubleHit",0.75,1.40,1.00),
    ]
    for name,sf,pf,df in scenarios:
        sd = demand * df
        ss = supply * sf
        gap=max(0.0, sd-ss)
        rar=gap*price
        ci=(pf-1.0)*sd*(price*0.2 if price else 1.0)
        si=1.0-(gap/sd) if sd>0 else 1.0
        re=min(1.0, risk_score/100.0)
        q("""INSERT INTO agent_scenarios(case_id,scenario_name,supply_factor,price_factor,demand_factor,
              gap_qty,revenue_at_risk,cost_impact,service_impact,risk_exposure,details)
              VALUES(:cid,:sn,:sf,:pf,:df,:gap,:rar,:ci,:si,:re,CAST(:d AS JSONB))""" ,
          cid=case_id,sn=name,sf=sf,pf=pf,df=df,gap=gap,rar=rar,ci=ci,si=si,re=re,
          d=json.dumps({"base_demand":demand,"base_supply":supply,"avg_price":price}))
