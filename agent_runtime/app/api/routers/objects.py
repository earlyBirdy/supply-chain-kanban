from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...db import one, all

router = APIRouter()


def _not_found(obj_type: str, obj_id: str):
    raise HTTPException(status_code=404, detail=f"{obj_type} not found: {obj_id}")


@router.get("/order/{order_id}")
def get_order(order_id: str):
    r = one("SELECT * FROM erp_orders WHERE order_id=:id", id=order_id)
    if not r:
        _not_found("Order", order_id)
    return {"type": "Order", **r}


@router.get("/shipment/{shipment_id}")
def get_shipment(shipment_id: str):
    r = one("SELECT * FROM wms_shipments WHERE shipment_id=:id", id=shipment_id)
    if not r:
        _not_found("Shipment", shipment_id)
    return {"type": "Shipment", **r}


@router.get("/production/{record_id}")
def get_production(record_id: str):
    r = one("SELECT * FROM mes_production WHERE record_id=:id", id=record_id)
    if not r:
        _not_found("ProductionRecord", record_id)
    return {"type": "ProductionRecord", **r}


@router.get("/resource/{resource_id}")
def get_resource(resource_id: str, limit: int = Query(50, ge=1, le=500)):
    # Resource is derived (market_signals are the canonical evidence)
    signals = all(
        """
        SELECT ts, signal_type, value, period
        FROM market_signals
        WHERE resource_id=:rid
        ORDER BY ts DESC
        LIMIT :lim
        """,
        rid=resource_id,
        lim=limit,
    )
    if not signals:
        _not_found("Resource", resource_id)
    latest = signals[0]
    return {
        "type": "Resource",
        "resource_id": resource_id,
        "latest_signal": latest,
        "signals": signals,
    }


@router.get("/list/orders")
def list_orders(limit: int = Query(50, ge=1, le=500)):
    return all("SELECT * FROM erp_orders ORDER BY ts DESC LIMIT :lim", lim=limit)


@router.get("/list/shipments")
def list_shipments(limit: int = Query(50, ge=1, le=500)):
    return all("SELECT * FROM wms_shipments ORDER BY ts DESC LIMIT :lim", lim=limit)


@router.get("/list/production")
def list_production(limit: int = Query(50, ge=1, le=500)):
    return all("SELECT * FROM mes_production ORDER BY ts DESC LIMIT :lim", lim=limit)


@router.get("/card/{card_id}")
def get_card(card_id: str, limit: int = Query(50, ge=1, le=500)):
    card = one("SELECT * FROM v_kanban_cards WHERE card_id=:id", id=card_id)
    if not card:
        _not_found("KanbanCard", card_id)

    edges = []

    # Link to Case (and its recs/actions)
    case_id = card.get("case_id")
    if case_id:
        c = one("SELECT * FROM agent_cases WHERE case_id=:cid", cid=case_id)
        if c:
            edges.append({"predicate": "represents", "to": {"type": "Case", **c}})
            recs = all(
                "SELECT * FROM agent_recommendations WHERE case_id=:cid ORDER BY rank ASC LIMIT :lim",
                cid=case_id,
                lim=limit,
            )
            acts = all(
                "SELECT * FROM agent_actions WHERE case_id=:cid ORDER BY created_at DESC LIMIT :lim",
                cid=case_id,
                lim=limit,
            )
            edges += [
                {"predicate": "recommends", "to": {"type": "Recommendation", **r}}
                for r in recs
            ]
            edges += [
                {"predicate": "executed", "to": {"type": "Action", **a}} for a in acts
            ]

    # Link to Resource evidence (latest signals)
    rid = card.get("resource_id")
    sigs = all(
        """
        SELECT ts, signal_type, value, period
        FROM market_signals
        WHERE resource_id=:rid
        ORDER BY ts DESC
        LIMIT :lim
        """,
        rid=rid,
        lim=min(limit, 50),
    )
    if sigs:
        edges.append(
            {
                "predicate": "about",
                "to": {"type": "Resource", "resource_id": rid, "latest_signal": sigs[0]},
            }
        )
        edges += [{"predicate": "signals", "to": {"type": "MarketSignal", **s}} for s in sigs]

    return {"node": {"type": "KanbanCard", **card}, "edges": edges}


@router.get("/list/cards")
def list_cards(
    status: Optional[str] = Query(None, description="todo|in_progress|blocked|resolved"),
    limit: int = Query(100, ge=1, le=500),
):
    if status:
        return all(
            "SELECT * FROM v_kanban_cards WHERE status=:st ORDER BY updated_at DESC LIMIT :lim",
            st=status,
            lim=limit,
        )
    return all("SELECT * FROM v_kanban_cards ORDER BY updated_at DESC LIMIT :lim", lim=limit)
