from fastapi.testclient import TestClient
import pytest

from app.api_main import create_app
from app.api.routers import operator as op_mod
from app.api.routers import demo as demo_mod


def test_operator_experience_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/experience_pack')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert 'data_center' in js['seed_packs']
    assert 'voltstream' in js['brands']


def test_operator_demo_script_and_screenshot_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_one(sql: str, **params):
        sl = sql.lower()
        if 'total_cards' in sl:
            return {'total_cards': 4, 'high_risk_cards': 2, 'approvals_waiting': 1, 'overdue_cards': 1, 'writebacks_24h': 2}
        if 'sum(revenue_at_risk)' in sl:
            return {'revenue_at_risk': 550000, 'cost_impact': 42000, 'gap_qty': 30, 'avg_service_impact': 4}
        if 'from agent_cases' in sl:
            return {'case_id': '11111111-1111-1111-1111-111111111111', 'status': 'AT_RISK', 'resource_id': 'dram_ddr5', 'risk_score': 94, 'confidence': 0.86, 'owner': 'dc_ops@demo'}
        if 'from v_kanban_cards' in sl:
            return {'card_id': 'aaaa', 'case_id': '11111111-1111-1111-1111-111111111111', 'title': 'DDR5 risk', 'status': 'todo', 'sla_state': 'at_risk', 'sla_remaining_hours': 4}
        return {}

    def fake_all(sql: str, **params):
        sl = sql.lower()
        if 'from v_kanban_cards' in sl:
            return [{'title': 'DDR5 risk', 'case_risk_score': 94, 'resource_id': 'dram_ddr5', 'assignee': 'dc_ops@demo', 'sla_state': 'at_risk'}]
        if 'from governed_writebacks' in sl:
            return [{'connector_name': 'erp_stub', 'target_system': 'erp.shipments', 'executions': 2, 'connector_family': 'erp', 'approval_policy': 'erp_high_impact', 'receipt_summary': 'Expedite', 'result_payload': {'receipt': {'change_ticket': 'CHG-1'}}, 'created_at': '2026-04-01T10:00:00Z', 'action_type': 'ExpediteShipment', 'external_ref': 'WB-1', 'status': 'ok'}]
        if 'from agent_recommendations' in sl:
            return [{'rank': 1, 'action_type': 'ExpediteShipment', 'rationale': 'Protect server builds'}]
        if 'from agent_scenarios' in sl:
            return [{'scenario_name': 'Expedite inbound shipment', 'service_impact': 4, 'cost_impact': 26, 'risk_exposure': 32}]
        if 'from v_pending_actions' in sl:
            return [{'pending_id': 'p1', 'status': 'pending', 'action_type': 'ExpediteShipment', 'rank': 0}]
        if 'from agent_actions' in sl:
            return [{'action_id': 'a1', 'action_type': 'PendingActionDecision', 'result': 'ok', 'created_at': '2026-04-01T10:00:00Z', 'audit': {'request_id': 'rid-1'}}]
        if 'from market_signals' in sl:
            return [{'signal_type': 'price_index_up', 'value': 12, 'period': '2025-W03'}]
        return []

    monkeypatch.setattr(op_mod, 'db_one', fake_one)
    monkeypatch.setattr(op_mod, 'db_all', fake_all)

    app = create_app()
    client = TestClient(app)
    r = client.get('/operator/demo_script?seed_pack=data_center&brand=datagrid')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['seed_pack_key'] == 'data_center'
    assert js['brand_key'] == 'datagrid'
    assert js['steps'][2]['ui_action'] == 'select_focus_case'

    r = client.get('/operator/screenshot_manifest?seed_pack=data_center&brand=datagrid')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert len(js['shots']) == 4
    assert 'Executive Overview' in js['shots'][0]['title']


def test_demo_reset_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(demo_mod, 'DEV_MODE', True)
    monkeypatch.setattr(demo_mod, '_exec_sql_script', lambda sql: calls.append(sql[:80]))
    app = create_app()
    client = TestClient(app)
    r = client.post('/demo/reset?pack=ev_launch')
    assert r.status_code == 200
    js = r.json()
    assert js['ok'] is True
    assert js['pack'] == 'ev_launch'
    assert js['seed_file'] == '01_seed_pack_ev_launch.sql'
    assert calls
