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
