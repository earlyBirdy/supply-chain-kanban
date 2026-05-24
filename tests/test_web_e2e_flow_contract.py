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
    assert 'Major Issues' in html
    assert 'Next Decision' in html
    assert 'function allVisibleCards' in app_js
    assert 'Project issues' in app_js
    assert 'Major issues sorted by risk.' in app_js
    assert 'issues visible' not in app_js


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

def test_web_has_simple_ai_leader_dashboard_contract() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    readme = (ROOT / 'README.md').read_text()

    assert 'AI Leader Dashboard' in html
    assert 'Forecast · inventory · partner KPI · actions' in html
    assert 'AI Agent Workbench' in html
    assert 'Semi-automated triage' in html
    assert 'function renderLeaderDashboard' in app_js
    assert 'function renderAgentQueue' in app_js
    assert "setStatus('Ready', 'ok')" in app_js
    assert 'Semi-automated Sense -> Recommend -> Execute + Prove triage' in readme


def test_web_default_brand_is_supply_chain_specific() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    experience = (ROOT / 'contracts/demo_experience_pack.yaml').read_text()

    assert 'Supply Chain AI Agent' in html
    assert 'Supply Chain AI Agent' in app_js
    assert 'Supply Chain AI Agent' in experience
    assert 'logo_mark: SCA' in experience
    assert 'Atlas Control' not in html
    assert 'Supply Chain Control Tower' not in html
    assert 'Supply Chain Control Tower' not in app_js
    assert 'Supply Chain Control Tower' not in experience
    assert 'Supply Chain by AI Agent' not in html
    assert 'Supply Chain by AI Agent' not in app_js
    assert 'Supply Chain by AI Agent' not in experience
    assert 'Atlas Grid' not in experience
    assert 'VoltStream Ops' not in experience
    assert 'EdgeForge Control' not in experience
    assert "brand.logo_mark || 'SCA'" in app_js


def test_web_renders_one_page_brief_loaded_from_api() -> None:
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'function renderBrief' in app_js
    assert 'function renderExecutive' in app_js
    assert 'loadExecutiveBrief' in app_js
    assert 'window.renderBrief = renderBrief' in app_js
    assert 'catch(err)' in app_js
    assert 'data-brief-ready' in app_js
    assert 'One-page operations brief' in app_js


def test_web_uses_normal_page_flow_to_avoid_overlapping_blocks() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    nginx = (ROOT / 'apps/web/nginx.conf').read_text()

    assert 'main{padding:14px 18px 28px; min-height:0;}' in html
    assert 'height:calc(100vh - 156px)' not in html
    assert 'overflow:visible' in html
    assert 'location = /app.js' in nginx
    assert 'Cache-Control "no-store, max-age=0"' in nginx
    assert '<script src="/app.js?v=0.24"></script>' in html

def test_web_removes_confusing_visible_status_copy() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'AI highlights blockers, approvals, and next actions.' in html
    assert '3 project issues visible' not in html
    assert 'simple AI leader dashboard + one-page E2E view' not in html
    assert 'simple AI leader dashboard + one-page E2E view' not in app_js
    assert 'Supply Chain by AI Agent · Professional Kanban operations surface.' not in html


def test_web_keeps_optional_loads_non_fatal_and_status_clear() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'Promise.allSettled([loadSummary(), loadExecutive(), loadExecutiveBrief(), loadDemoScript()])' in app_js
    assert 'async function safeLoad' in app_js
    assert "loadScreenshotManifest(){ const data = await safeLoad" in app_js
    assert "if(window.renderBrief) window.renderBrief();" in app_js
    assert 'Load failed' not in html
    assert 'Load failed' not in app_js


def test_web_selection_badge_hides_raw_case_uuid() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'No issue selected' in html
    assert 'Selected: ${shortText(selectedTitle, 34)}' in app_js
    assert '<div class="field-label">Issue</div>' in app_js
    assert 'Selection: ${c.case_id' not in app_js
    assert 'Selection: none' not in html
    assert 'Selection: none' not in app_js
