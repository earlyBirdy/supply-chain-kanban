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
    assert "location.port === '8080' || !isLocalHost" in app_js
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
    assert 'Major issues' in app_js
    assert 'Showing top ${MAJOR_ISSUE_LIMIT} major issues' in app_js
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
    assert '<script src="/app.js?v=0.30"></script>' in html

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

    assert 'Promise.allSettled([loadSummary(), loadExecutive(), loadExecutiveBrief(), loadDemoScript(), loadNews()])' in app_js
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


def test_web_has_existing_system_integration_and_templates() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    readme = (ROOT / 'README.md').read_text()

    assert 'Supply Chain AI Agent' in html
    assert 'Connect Existing Systems' in html
    assert 'ERP / WMS / MES / TMS / Supplier Portal / CSV reports' in html
    assert 'ontology objects → AI risk prediction → major issues' in html
    assert 'Read-only first · governed writeback after approval' in html
    assert 'Ontology Decision Map' in html
    assert 'Power Templates' in html
    assert 'News + Market Data' in app_js
    assert 'Blockchain Evidence' in app_js
    assert 'function renderOntologyMap' in app_js
    assert 'ForecastPlan' in app_js
    assert 'AgentDecision' in app_js
    assert 'Commodity shock' in app_js
    assert 'Supplier OTIF rescue' in app_js
    assert 'Inventory rebalance' in app_js
    assert 'function renderIntegrationHub' in app_js
    assert 'function renderFeatureTemplates' in app_js
    assert 'Power Templates' in readme


def test_web_tracks_commodity_news_for_arrangements() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    compose = (ROOT / 'docker-compose.yml').read_text()
    rss = (ROOT / 'apps/news_monitor/app/rss_sources.yaml').read_text()
    news_router = (ROOT / 'apps/api/app/api/routers/news.py').read_text()

    assert 'Live News for Commodity Arrangements' in html
    assert 'btnNewsDemo' in html
    assert 'function renderNewsMonitor' in app_js
    assert 'function triggerCommodityNews' in app_js
    assert '/news/items?topic=commodities&limit=6' in app_js
    assert '/news/check-now?topic=commodities' in app_js
    assert 'NEWS_TOPIC: commodities' in compose
    assert 'lithium battery materials' in rss
    assert 'freight port disruption' in rss
    assert 'LFP battery material shipment delay' in news_router
    assert 'review buy timing' in app_js


def test_web_keeps_integrations_and_templates_as_subpages() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'id="pageProject" data-page="project-status"' in html
    assert 'id="pageIntegrations" data-page="integrations"' in html
    assert 'id="pageTemplates" data-page="templates-news"' in html
    assert '<button class="ghost" id="btnPageIntegrations">Integrations</button>' in html
    assert 'function showPage' in app_js
    assert "showPage('project')" in app_js
    assert "showPage('integrations')" in app_js
    assert "showPage('templates')" in app_js
    assert html.index('id="pageProject"') < html.index('id="pageIntegrations"')
    assert html.index('id="pageProject"') < html.index('id="pageTemplates"')


def test_web_project_status_shows_top_major_issues_not_full_backlog() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()

    assert 'One-page view · top issues only · grouped backlog below.' in html
    assert 'const MAJOR_ISSUE_LIMIT = 4' in app_js
    assert 'function majorIssueCards' in app_js
    assert 'lower-priority signals grouped' in app_js
    assert 'Showing top ${MAJOR_ISSUE_LIMIT} major issues' in app_js
    assert '<script src="/app.js?v=0.30"></script>' in html


def test_hugging_face_space_demo_contract() -> None:
    dockerfile = (ROOT / 'Dockerfile.hf').read_text()
    start = (ROOT / 'scripts/hf_start.sh').read_text()
    docs = (ROOT / 'docs/demo/HUGGING_FACE_SPACE.md').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    api_main = (ROOT / 'apps/api/app/api_main.py').read_text()

    assert 'EXPOSE 7860' in dockerfile
    assert 'SUPPLY_CHAIN_SERVE_WEB=1' in dockerfile
    assert 'COPY apps/web/public /app/web' in dockerfile
    assert 'uvicorn app.api_main:app --host 0.0.0.0 --port "$API_PORT"' in start
    assert '_include_api("/api")' in api_main
    assert 'StaticFiles(directory=web_dir, html=True)' in api_main
    assert "location.port === '8080' || !isLocalHost" in app_js
    assert 'Docker Space' in docs


def test_ontology_contract_supports_ai_agent_erp_mes_news_blockchain_map() -> None:
    ontology = (ROOT / 'contracts/supply_chain_ontology.yaml').read_text()
    readme = (ROOT / 'README.md').read_text()
    blueprint = (ROOT / 'docs/product/ONTOLOGY_INTEGRATION_BLUEPRINT.md').read_text()

    for token in [
        'ForecastPlan:',
        'InventoryPosition:',
        'PartnerPerformanceMetric:',
        'NewsRiskSignal:',
        'AgentDecision:',
        'integration_model:',
        'BlockchainEvidence:',
        'read_only_first_then_approval_gated_writeback',
    ]:
        assert token in ontology

    assert 'docs/product/ONTOLOGY_INTEGRATION_BLUEPRINT.md' in readme
    assert 'ERP/MES/WMS/TMS/Supplier/CSV/News' in blueprint
    assert 'approval-gated writeback' in blueprint
    assert 'blockchain-ready proof' in blueprint


def test_agent_skills_and_autoresearch_playbook_contract() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    readme = (ROOT / 'README.md').read_text()
    playbook = (ROOT / 'docs/product/AGENT_SKILLS_AND_AUTORESEARCH_PLAYBOOK.md').read_text()

    assert 'skill-driven triage' in html
    assert 'bounded risk experiments' in html
    assert '<script src="/app.js?v=0.30"></script>' in html
    assert 'Agent Skill Playbook' in app_js
    assert 'Autoresearch Sandbox' in app_js
    assert 'Agent skill triage' in app_js
    assert 'Autoresearch risk sprint' in app_js
    assert 'docs/product/AGENT_SKILLS_AND_AUTORESEARCH_PLAYBOOK.md' in readme
    assert 'Skill playbook' in readme
    assert 'Autoresearch loop' in readme
    assert 'bounded experiment process' in playbook
    assert 'EvidenceReceipt / blockchain-ready proof' in playbook


def test_patch_checklist_wording_is_explicit() -> None:
    html = (ROOT / 'apps/web/public/index.html').read_text()
    app_js = (ROOT / 'apps/web/public/app.js').read_text()
    readme = (ROOT / 'README.md').read_text()
    blueprint = (ROOT / 'docs/product/ONTOLOGY_INTEGRATION_BLUEPRINT.md').read_text()
    playbook = (ROOT / 'docs/product/AGENT_SKILLS_AND_AUTORESEARCH_PLAYBOOK.md').read_text()

    combined = '\n'.join([html, app_js, readme, blueprint, playbook])
    for token in [
        'Ontology-first positioning',
        'real-world supply-chain objects instead of only showing ERP/MES/WMS rows',
        'orders, suppliers, plants, forecasts, inventory positions, partner metrics, news risks, and agent decisions',
        'source systems feeding the ontology layer',
        'not as the final user experience',
        'ingest system data',
        'map to ontology',
        'detect risks',
        'predict disruptions',
        'recommend actions',
        'require human approval',
        'create writeback receipt',
        'traceable receipts',
        'decision hashes',
        'tamper-resistant evidence',
        'not a required runtime dependency',
        'Commodity, supplier, logistics, and geopolitical risk signals',
        'product/design patterns',
        'without heavy runtime dependencies',
    ]:
        assert token in combined
