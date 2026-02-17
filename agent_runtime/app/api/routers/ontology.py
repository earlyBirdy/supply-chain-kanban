import json

import yaml
from fastapi import APIRouter, Response

from ...ontology_store import load_ontology
from ...policy_store import load_policy, policy_etag, policy_revision

router = APIRouter()


@router.get("/")
def get_ontology():
    """Return ontology plus the currently effective governance policy."""
    p = load_policy()
    return {"ontology": load_ontology(), "policy": p, "policy_meta": {"etag": policy_etag(p), "revision": policy_revision(p)}}


@router.get("/json")
def get_ontology_json():
    p = load_policy()
    payload = {"ontology": load_ontology(), "policy": p, "policy_meta": {"etag": policy_etag(p), "revision": policy_revision(p)}}
    return Response(content=json.dumps(payload, ensure_ascii=False, indent=2), media_type="application/json; charset=utf-8")


@router.get("/yaml")
def get_ontology_yaml():
    p = load_policy()
    payload = {"ontology": load_ontology(), "policy": p, "policy_meta": {"etag": policy_etag(p), "revision": policy_revision(p)}}
    return Response(content=yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), media_type="text/yaml; charset=utf-8")
