def score_decisions(risk: int):
    recs=[]
    svc=90 if risk>=70 else 75; cost=65 if risk>=85 else 80; rsk=70 if risk>=85 else 60
    ds=int(round(0.4*svc+0.35*cost+0.25*rsk))
    recs.append(("prioritize_allocation", {"note":"Protect critical products first"}, svc, cost, rsk, ds))
    svc=80 if risk>=70 else 70; cost=70 if risk>=70 else 85; rsk=65 if risk>=70 else 55
    ds=int(round(0.4*svc+0.35*cost+0.25*rsk))
    recs.append(("inventory_buffer", {"note":"Increase safety stock / rebalance DCs"}, svc, cost, rsk, ds))
    recs.sort(key=lambda x: x[-1], reverse=True)
    return recs
