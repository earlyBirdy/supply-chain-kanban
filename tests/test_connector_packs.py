from app.connectors.governed_writeback import get_governed_writeback_adapter


def test_governed_writeback_routes_to_supplier_portal() -> None:
    adapter = get_governed_writeback_adapter()
    preview = adapter.preview(action_type='OpenSupplierTicket', payload={'supplier_id': 'SUP_B'})
    result = adapter.execute(action_type='OpenSupplierTicket', payload={'supplier_id': 'SUP_B'}).as_dict()
    assert preview['connector_family'] == 'supplier_portal'
    assert result['connector_family'] == 'supplier_portal'
    assert result['connector_name'] == 'supplier_portal_stub'
    assert result['receipt']['receipt_type'] == 'supplier_escalation'


def test_governed_writeback_routes_to_ticketing() -> None:
    adapter = get_governed_writeback_adapter()
    preview = adapter.preview(action_type='CreateOpsTicket', payload={'resource_id': 'industrial_ethernet_switch'})
    result = adapter.execute(action_type='CreateOpsTicket', payload={'resource_id': 'industrial_ethernet_switch'}).as_dict()
    assert preview['target_system'] == 'ticketing.incidents'
    assert result['connector_family'] == 'ticketing'
    assert result['connector_name'] == 'ticketing_stub'
    assert result['receipt']['approval_checkpoint'] == 'ticketing_internal_coordination'
