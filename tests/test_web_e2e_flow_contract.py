from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_web_has_e2e_milestone_flow_controls() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'E2E release flow: supplier signal to final OQC release' in html
    assert 'btnFlowFirstIssue' in html
    assert 'flowInsight' in html
    assert 'function renderFlowInsight' in app_js
    assert 'function focusFirstFlowIssue' in app_js
    assert 'Final release: confirm OQC evidence' in app_js


def test_web_api_proxy_contract_for_local_e2e() -> None:
    nginx = (ROOT / 'apps/web/nginx.conf').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    api_main = (ROOT / 'apps/api/app/api_main.py').read_text()

    assert 'location /api/' in nginx
    assert 'proxy_pass http://api:8000/;' in nginx
    assert "location.port === '8080' ? sameOriginApiBase" in app_js
    assert 'CORSMiddleware' in api_main
    assert 'http://localhost:8080' in api_main


def test_web_is_one_page_project_e2e_layout() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'data-layout="one-page-project-e2e"' in html
    assert 'Project E2E Flow' in html
    assert 'Project Action Queue' in html
    assert 'Next Decision' in html
    assert 'function allVisibleCards' in app_js
    assert 'Project issues' in app_js
    assert 'one-page E2E view' in app_js


def test_web_explains_ai_agent_blockchain_trust_rail() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    readme = (ROOT / 'README.md').read_text()

    assert 'agentTrustRail' in html
    assert 'AI Agent Brain + Hands' in html
    assert 'Blockchain Judge + Vault' in html
    assert 'Autonomous M2M Settlement' in html
    assert 'function renderAgentTrustRail' in app_js
    assert 'autoSelectFirstProjectIssue' in app_js
    assert 'AI agents + blockchain convergence' in readme
    assert 'tamper-evident source of truth' in readme
