import json, requests
from .config import SLACK_WEBHOOK_URL
from .db import q

def upsert_case(resource_id: str, risk_score: int, confidence: float, ltf_days: int, features: dict):
    ex=q("""SELECT case_id FROM agent_cases WHERE status IN ('AT_RISK','MITIGATION') AND resource_id=:rid
             ORDER BY updated_at DESC LIMIT 1""", rid=resource_id).fetchone()
    if ex:
        cid=str(ex[0])
        q("""UPDATE agent_cases SET updated_at=now(), risk_score=:r, confidence=:c, lead_time_to_failure_days=:ltf,
             root_signals=CAST(:f AS JSONB) WHERE case_id=:cid""", r=risk_score,c=confidence,ltf=ltf_days,f=json.dumps(features),cid=cid)
        return cid, False
    row=q("""INSERT INTO agent_cases(resource_id,risk_score,confidence,lead_time_to_failure_days,root_signals)
             VALUES(:rid,:r,:c,:ltf,CAST(:f AS JSONB)) RETURNING case_id""", rid=resource_id,r=risk_score,c=confidence,ltf=ltf_days,f=json.dumps(features)).fetchone()
    return str(row[0]), True

def write_recommendations(case_id: str, recs: list):
    q("""DELETE FROM agent_recommendations WHERE case_id=:cid""", cid=case_id)
    for i,(at,payload,svc,cost,rsk,ds) in enumerate(recs, start=1):
        q("""INSERT INTO agent_recommendations(case_id,rank,action_type,action_payload,service_score,cost_score,risk_score,decision_score)
             VALUES(:cid,:rk,:at,CAST(:ap AS JSONB),:ss,:cs,:rs,:ds)""", cid=case_id,rk=i,at=at,ap=json.dumps(payload),ss=svc,cs=cost,rs=rsk,ds=ds)

def slack_alert(case_id: str, resource_id: str, risk_score: int, top_action: str):
    if not SLACK_WEBHOOK_URL: return "skipped(no_webhook)"
    text=f"🚨 Emerging constraint: *{resource_id}* risk={risk_score} case={case_id}\nTop action: `{top_action}`"
    r=requests.post(SLACK_WEBHOOK_URL, json={"text":text}, timeout=10)
    return "ok" if r.status_code<300 else f"failed({r.status_code})"
