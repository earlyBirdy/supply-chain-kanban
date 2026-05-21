import json
import time
from .config import POLL_SECONDS, RISK_CREATE_THRESHOLD, ALERT_THRESHOLD
from .ingest import run_all as ingest_all
from .dq import run_blocking_gates
from .signals import load_latest_market_signals, load_supplier_otif_latest
from .risk_model import compute_risk
from .decision import score_decisions
from .actions import upsert_case, write_recommendations, slack_alert
from .scenarios import persist_scenarios
from .db import q, wait_for_db
from .audit import with_audit

def tick():
    ing=ingest_all()
    print("Ingested:", ing, flush=True)

    if not run_blocking_gates():
        print("DQ BLOCK: skipping case creation this tick", flush=True)
        return

    market=load_latest_market_signals()
    otif=load_supplier_otif_latest()

    for rid, sigs in market.items():
        risk, conf, ltf, features = compute_risk(sigs, otif)
        q("""INSERT INTO agent_predictions(resource_id,risk_score,confidence,predicted_window_days,features)
             VALUES(:rid,:r,:c,:w,CAST(:f AS JSONB))""", rid=rid, r=risk, c=conf, w=ltf, f=json.dumps(features))

        if risk < RISK_CREATE_THRESHOLD:
            continue

        case_id,_=upsert_case(rid, risk, conf, ltf, features)
        persist_scenarios(case_id, risk)
        recs=score_decisions(risk)
        write_recommendations(case_id, recs)

        if risk >= ALERT_THRESHOLD:
            top=recs[0][0] if recs else "none"
            res=slack_alert(case_id, rid, risk, top)
            pl = with_audit(
                {},
                actor={"sub": "system", "role": "system"},
                request=None,
                request_path="job:runner",
                request_method="tick",
                materialization_id="",
            )
            q(
                """INSERT INTO agent_actions(case_id,channel,action_type,payload,result)
                     VALUES(:cid,'slack','alert',CAST(:pl AS JSONB),:res)""",
                cid=case_id,
                pl=json.dumps(pl, default=str),
                res=res,
            )

def main():
    wait_for_db(max_seconds=90)
    while True:
        try:
            tick()
        except Exception as e:
            print("Agent tick failed:", repr(e), flush=True)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
