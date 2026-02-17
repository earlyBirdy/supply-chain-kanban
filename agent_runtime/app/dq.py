import json
from .db import q, one

def _ins(g, s, p, scope, msg, details=None):
    q("""INSERT INTO dq_results(gate_name,severity,passed,scope,message,details)
          VALUES(:g,:s,:p,CAST(:scope AS JSONB),:m,CAST(:details AS JSONB))""",
      g=g,s=s,p=p,scope=json.dumps(scope),m=msg,details=json.dumps(details or {}))

def run_blocking_gates():
    ok=True
    r=one("""SELECT COUNT(*) AS c FROM erp_orders WHERE qty < 0""")
    if r and r["c"]>0:
        ok = False
        _ins("erp_no_negative_qty","BLOCK",False,{"table":"erp_orders"},"Found negative qty",{"count":r["c"]})
    else:
        _ins("erp_no_negative_qty","BLOCK",True,{"table":"erp_orders"},"OK")

    r=one("""SELECT COUNT(*) AS c FROM ops_signals WHERE metric='otif' AND (value<0 OR value>1 OR value IS NULL)""")
    if r and r["c"]>0:
        ok = False
        _ins("otif_range_0_1","BLOCK",False,{"table":"ops_signals","metric":"otif"},"Invalid OTIF",{"count":r["c"]})
    else:
        _ins("otif_range_0_1","BLOCK",True,{"table":"ops_signals","metric":"otif"},"OK")

    r=one("""SELECT COUNT(*) AS c FROM wms_shipments WHERE delivered_qty > ordered_qty*1.5""")
    if r and r["c"]>0:
        _ins("wms_qty_sanity","WARN",False,{"table":"wms_shipments"},"Delivered qty unusually high",{"count":r["c"]})
    else:
        _ins("wms_qty_sanity","WARN",True,{"table":"wms_shipments"},"OK")

    return ok
