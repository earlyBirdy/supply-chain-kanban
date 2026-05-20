from __future__ import annotations


import pytest

import app.execution as exec_mod


def test_execute_action_persists_governed_writeback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    class FakeRow:
        def __getitem__(self, idx):
            return 'a1'

    class FakeResult:
        def fetchone(self):
            return FakeRow()

    def fake_q(sql: str, **params):
        calls.append((sql.lower(), params))
        return FakeResult()

    monkeypatch.setattr(exec_mod, 'q', fake_q)
    monkeypatch.setattr(exec_mod, 'one', lambda *a, **k: {'risk_score': 80, 'card_id': 'k1', 'case_id': 'c1', 'status': 'todo'})

    class FakeAdapter:
        def preview(self, **kwargs):
            return {'adapter': 'governed_writeback', 'target_system': 'erp.shipments', 'policy_gate': 'approved_action_required'}
        def execute(self, **kwargs):
            class R:
                def as_dict(self):
                    return {
                        'ok': True,
                        'message': 'mock-executed ExpediteShipment',
                        'connector_name': 'mock',
                        'adapter_name': 'governed_writeback',
                        'target_system': 'erp.shipments',
                        'external_ref': 'WB-123',
                        'policy_gate': 'approved_action_required',
                        'approval_state': 'executed',
                        'connector_data': {'payload': kwargs.get('payload')},
                    }
            return R()

    monkeypatch.setattr(exec_mod, 'get_governed_writeback_adapter', lambda: FakeAdapter())

    res = exec_mod.execute_action(
        case_id='c1',
        channel='supervisor',
        action_type='ExpediteShipment',
        payload={'resource_id': 'dram_ddr5', 'pending_id': 'p1'},
        dry_run=False,
    )

    assert res['ok'] is True
    assert res['writeback']['external_ref'] == 'WB-123'
    assert any('insert into governed_writebacks' in sql for sql, _ in calls)
