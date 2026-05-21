from fastapi import APIRouter, HTTPException, Query

from ...db import all, one

router = APIRouter()


@router.get("/neighbors")
def neighbors(
    object_type: str = Query(..., description="Order|Shipment|ProductionRecord|Case|KanbanCard|Resource"),
    object_id: str = Query(..., description="ID of the object"),
    limit: int = Query(50, ge=1, le=500),
):
    """Lightweight graph expansion.

    This is a demo alternative to a full graph engine: it resolves key relationships
    defined in the ontology using joins on canonical tables.
    """

    t = object_type.lower()
    if t == "order":
        order = one("SELECT * FROM erp_orders WHERE order_id=:id", id=object_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        ships = all(
            "SELECT * FROM wms_shipments WHERE order_id=:oid ORDER BY ts DESC LIMIT :lim",
            oid=object_id,
            lim=limit,
        )
        return {
            "node": {"type": "Order", **order},
            "edges": [
                {"predicate": "fulfills", "to": {"type": "Shipment", **s}} for s in ships
            ],
        }

    if t == "shipment":
        sh = one("SELECT * FROM wms_shipments WHERE shipment_id=:id", id=object_id)
        if not sh:
            raise HTTPException(status_code=404, detail="Shipment not found")
        edges = []
        if sh.get("order_id"):
            o = one("SELECT * FROM erp_orders WHERE order_id=:oid", oid=sh["order_id"])
            if o:
                edges.append({"predicate": "fulfills", "to": {"type": "Order", **o}})
        return {"node": {"type": "Shipment", **sh}, "edges": edges}

    if t in ("productionrecord", "production"):
        pr = one("SELECT * FROM mes_production WHERE record_id=:id", id=object_id)
        if not pr:
            raise HTTPException(status_code=404, detail="ProductionRecord not found")
        return {"node": {"type": "ProductionRecord", **pr}, "edges": []}

    if t == "case":
        c = one("SELECT * FROM agent_cases WHERE case_id=:id", id=object_id)
        if not c:
            raise HTTPException(status_code=404, detail="Case not found")
        recs = all(
            "SELECT * FROM agent_recommendations WHERE case_id=:cid ORDER BY rank ASC LIMIT :lim",
            cid=object_id,
            lim=limit,
        )
        acts = all(
            "SELECT * FROM agent_actions WHERE case_id=:cid ORDER BY created_at DESC LIMIT :lim",
            cid=object_id,
            lim=limit,
        )
        return {
            "node": {"type": "Case", **c},
            "edges": (
                [{"predicate": "recommends_for", "to": {"type": "Recommendation", **r}} for r in recs]
                + [{"predicate": "executed_for", "to": {"type": "Action", **a}} for a in acts]
            ),
        }

    
    if t in ("card", "kanbancard"):
        k = one("SELECT * FROM v_kanban_cards WHERE card_id=:id", id=object_id)
        if not k:
            raise HTTPException(status_code=404, detail="KanbanCard not found")
        edges = []
        if k.get("case_id"):
            c = one("SELECT * FROM agent_cases WHERE case_id=:cid", cid=k["case_id"])
            if c:
                edges.append({"predicate": "represents", "to": {"type": "Case", **c}})
                recs = all(
                    "SELECT * FROM agent_recommendations WHERE case_id=:cid ORDER BY rank ASC LIMIT :lim",
                    cid=k["case_id"],
                    lim=limit,
                )
                acts = all(
                    "SELECT * FROM agent_actions WHERE case_id=:cid ORDER BY created_at DESC LIMIT :lim",
                    cid=k["case_id"],
                    lim=limit,
                )
                edges += [{"predicate": "recommends", "to": {"type": "Recommendation", **r}} for r in recs]
                edges += [{"predicate": "executed", "to": {"type": "Action", **a}} for a in acts]

        # Resource link
        rid = k.get("resource_id")
        sigs = all(
            "SELECT ts, signal_type, value, period FROM market_signals WHERE resource_id=:rid ORDER BY ts DESC LIMIT :lim",
            rid=rid,
            lim=min(limit, 50),
        )
        if sigs:
            edges.append({"predicate": "about", "to": {"type": "Resource", "resource_id": rid}})
            edges += [{"predicate": "signals", "to": {"type": "MarketSignal", **s}} for s in sigs]

        return {"node": {"type": "KanbanCard", **k}, "edges": edges}

    if t == "resource":
        sigs = all(
            "SELECT ts, signal_type, value, period FROM market_signals WHERE resource_id=:rid ORDER BY ts DESC LIMIT :lim",
            rid=object_id,
            lim=limit,
        )
        if not sigs:
            raise HTTPException(status_code=404, detail="Resource not found")
        return {
            "node": {"type": "Resource", "resource_id": object_id},
            "edges": [{"predicate": "signals", "to": {"type": "MarketSignal", **s}} for s in sigs],
        }

    raise HTTPException(status_code=400, detail=f"Unsupported object_type: {object_type}")
