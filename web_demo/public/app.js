(function(){
  const out = document.getElementById('out');
  const conn = document.getElementById('conn');
  const topicEl = document.getElementById('topic');

  const apiBase = (location.protocol + '//' + location.hostname + ':8000');
  const wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host.replace(':8080', ':8081') + '/ws';
  document.getElementById('wsUrl').textContent = wsUrl;

  const promptEl = document.getElementById('prompt');
  const chat = document.getElementById('chat');
  const btnSend = document.getElementById('btnSend');
  const grounded = document.getElementById('grounded');
  let lastGrounded = null;  function escapeHtml(s){
    return String(s||'')
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;');
  }

  function renderMarkdown(md){
    // Minimal, safe-ish markdown renderer for our strict template.
    const lines = String(md||'').split(/\r?\n/);
    let html = '';
    let inUl = false;
    let inOl = false;

    function closeLists(){
      if(inUl){ html += '</ul>'; inUl = false; }
      if(inOl){ html += '</ol>'; inOl = false; }
    }

    for(const raw of lines){
      const line = escapeHtml(raw);

      // Headings (###)
      const h3 = line.match(/^###\s+(.*)$/);
      if(h3){
        closeLists();
        html += `<h3>${h3[1]}</h3>`;
        continue;
      }

      // Ordered list: "1. ..."
      const ol = line.match(/^\s*\d+\.\s+(.*)$/);
      if(ol){
        if(inUl){ html += '</ul>'; inUl = false; }
        if(!inOl){ html += '<ol>'; inOl = true; }
        html += `<li>${ol[1]}</li>`;
        continue;
      }

      // Unordered list: "- ..."
      const ul = line.match(/^\s*-\s+(.*)$/);
      if(ul){
        if(inOl){ html += '</ol>'; inOl = false; }
        if(!inUl){ html += '<ul>'; inUl = true; }
        html += `<li>${ul[1]}</li>`;
        continue;
      }

      // Blank line
      if(line.trim() === ''){
        closeLists();
        html += '<div style="height:6px;"></div>';
        continue;
      }

      closeLists();
      html += `<div>${line}</div>`;
    }
    closeLists();

    // Inline formatting: **bold**, `code`, [text](url)
    html = html
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Bracket labels like [A1] can be emphasized slightly
    html = html.replace(/\[(A|N|C)\d+\]/g, '<code>$&</code>');
    return html;
  }

  function appendChat(role, text){
    if(!chat) return;
    const box = document.createElement('div');
    box.className = 'msg ' + (role === 'model' ? 'model' : 'user');

    const roleEl = document.createElement('div');
    roleEl.className = 'role';
    roleEl.textContent = role === 'model' ? 'Gemini' : 'You';

    const content = document.createElement('div');
    content.className = 'content';

    if(role === 'model'){
      content.innerHTML = renderMarkdown(text);
    } else {
      content.textContent = String(text||'').trim();
    }

    box.appendChild(roleEl);
    box.appendChild(content);

    // prepend newest on top
    if(chat.firstChild) chat.insertBefore(box, chat.firstChild);
    else chat.appendChild(box);
  }


  function log(obj){
    const s = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
    out.textContent = s + "\n\n" + out.textContent;
  }

  function fmtTs(ts){
    if(!ts) return '';
    try { return new Date(ts).toLocaleString(); } catch { return String(ts); }
  }

  function setStatus(id, msg, cls){
    const el = document.getElementById(id);
    if(!el) return;
    el.textContent = msg || '';
    el.className = 'small ' + (cls || '');
  }

  function esc(s){
    return String(s ?? '').replace(/[&<>"']/g, (c)=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
  }

  function renderTable(tbody, rowsHtml){
    tbody.innerHTML = rowsHtml || '<tr><td colspan="4" class="small">No data</td></tr>';
  }

  function renderGrounded(summary){
    lastGrounded = summary || null;
    if(!grounded) return;
    if(!summary){
      grounded.innerHTML = '<div class="small">No grounded evidence yet.</div>';
      return;
    }
    function section(title, arr){
      if(!arr || !arr.length) return '';
      const rows = arr.map(r => {
        const label = esc(r.label || '');
        const t = esc(r.title || '');
        const ts = esc(fmtTs(r.ts || ''));
        const score = (r.score === null || r.score === undefined) ? '' : esc(String(r.score));
        const url = r.url ? `<a href="${esc(r.url)}" target="_blank">link</a>` : '';
        return `<tr><td><span class="pill">[${label}]</span></td><td>${ts}</td><td>${score}</td><td>${t}</td><td>${url}</td></tr>`;
      }).join('');
      return `
        <div style="margin-top:10px;">
          <div style="font-weight:600; color:#e2e8f0; margin:6px 0;">${esc(title)}</div>
          <table>
            <thead><tr><th>Label</th><th>TS</th><th>Score</th><th>Title</th><th>URL</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
    }
    grounded.innerHTML = [
      section('Alerts', summary.alerts),
      section('News', summary.news),
      section('Cases', summary.cases),
      (!summary.alerts?.length && !summary.news?.length && !summary.cases?.length) ? '<div class="small">No evidence.</div>' : ''
    ].join('');
  }

  async function fetchJson(path){
    const url = apiBase + path;
    const res = await fetch(url);
    if(!res.ok){
      const txt = await res.text();
      throw new Error(res.status + ' ' + res.statusText + ': ' + txt);
    }
    return await res.json();
  }

  async function refreshCases(){
    const topic = (topicEl.value || 'memory').trim();
    setStatus('casesStatus', 'Loading…', 'warn');
    try{
      const data = await fetchJson('/cases?limit=20');
      const tbody = document.querySelector('#casesTable tbody');
      const rows = (data || []).slice(0, 20).map(c => {
        const summary = esc(c.summary || c.title || c.case_type || '');
        const status = esc(c.status || '');
        const cid = esc(c.case_id || '');
        const updated = fmtTs(c.updated_at || c.created_at);
        return `<tr>
          <td>${esc(updated)}</td>
          <td><span class="pill">${cid}</span></td>
          <td>${status}</td>
          <td>${summary}</td>
        </tr>`;
      }).join('');
      renderTable(tbody, rows);
      setStatus('casesStatus', `OK • ${data.length} cases`, 'ok');
      log({type:'ui', action:'refresh_cases', count: data.length, topic});
    }catch(e){
      setStatus('casesStatus', 'Error: ' + e.message, 'err');
      log({type:'error', action:'refresh_cases', error: String(e)});
    }
  }

  async function refreshAlerts(){
    const topic = (topicEl.value || 'memory').trim();
    setStatus('alertsStatus', 'Loading…', 'warn');
    try{
      const data = await fetchJson(`/news/alerts?topic=${encodeURIComponent(topic)}&limit=20`);
      const tbody = document.querySelector('#alertsTable tbody');
      const rows = (data || []).slice(0, 20).map(a => {
        const sev = esc(a.severity ?? '');
        const title = esc(a.title ?? a.signal ?? '');
        const src = esc(a.source ?? a.url ?? '');
        const ts = fmtTs(a.ts || a.created_at);
        return `<tr>
          <td>${esc(ts)}</td>
          <td><span class="pill">${sev}</span></td>
          <td>${title}</td>
          <td>${src}</td>
        </tr>`;
      }).join('');
      renderTable(tbody, rows);
      setStatus('alertsStatus', `OK • ${data.length} alerts`, 'ok');
      log({type:'ui', action:'refresh_alerts', count: data.length, topic});
    }catch(e){
      setStatus('alertsStatus', 'Error: ' + e.message, 'err');
      log({type:'error', action:'refresh_alerts', error: String(e)});
    }
  }

  async function refreshNews(){
    const topic = (topicEl.value || 'memory').trim();
    setStatus('newsStatus', 'Loading…', 'warn');
    try{
      const data = await fetchJson(`/news/items?topic=${encodeURIComponent(topic)}&limit=30`);
      const tbody = document.querySelector('#newsTable tbody');
      const rows = (data || []).slice(0, 30).map(n => {
        const score = esc(n.score ?? '');
        const title = esc(n.title ?? '');
        const src = esc(n.source ?? n.url ?? '');
        const ts = fmtTs(n.published_at || n.ts || n.created_at);
        return `<tr>
          <td>${esc(ts)}</td>
          <td><span class="pill">${score}</span></td>
          <td><a href="${esc(n.url || '#')}" target="_blank">${title || '(untitled)'}</a></td>
          <td>${src}</td>
        </tr>`;
      }).join('');
      renderTable(tbody, rows);
      setStatus('newsStatus', `OK • ${data.length} items`, 'ok');
      log({type:'ui', action:'refresh_news', count: data.length, topic});
    }catch(e){
      setStatus('newsStatus', 'Error: ' + e.message, 'err');
      log({type:'error', action:'refresh_news', error: String(e)});
    }
  }

  let ws;
  function connect(){
    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      conn.textContent = 'WS: connected';
      log({type:'system', message:'connected'});
    };
    ws.onclose = () => {
      conn.textContent = 'WS: disconnected';
      setTimeout(connect, 1000);
    };
    ws.onerror = (e) => { log({type:'error', message:'ws error', e: String(e)}); };
    ws.onmessage = (ev) => {
      let msg = null;
      try { msg = JSON.parse(ev.data); } catch { log(ev.data); return; }
      log(msg);

      const t = msg.type || '';
      if(t === 'gemini_live'){
        const st = msg.status || 'unknown';
        if(st === 'connected') setStatus('geminiStatus', 'Gemini: connected', 'ok');
        else setStatus('geminiStatus', 'Gemini: ' + st, 'warn');
      }
      if(t === 'gemini_text'){
        appendChat('model', msg.text || '');
      }
      if(t === 'grounded_summary'){
        renderGrounded(msg.summary || null);
        const a = (msg.summary && msg.summary.alerts) ? msg.summary.alerts.length : 0;
        const n = (msg.summary && msg.summary.news) ? msg.summary.news.length : 0;
        const c = (msg.summary && msg.summary.cases) ? msg.summary.cases.length : 0;
        appendChat('evidence', `alerts=${a}, news=${n}, cases=${c}`);
      }
      if(t === 'tool_results'){
        // Show a compact tool summary in chat so it's obvious we grounded the response.
        const tools = (msg.results && msg.results.tools) ? msg.results.tools : [];
        const summary = tools.map(x => `${x.ok ? '✓' : '✗'} ${x.name}`).join(', ');
        if(summary) appendChat('tools', summary);
      }
      if(t === 'error'){
        appendChat('error', msg.message || 'error');
      }
      if(t === 'hello'){
        appendChat('system', msg.message || 'connected');
      }
    };
  }
  connect();

  function send(cmd, extra){
    const payload = Object.assign({type:'command', command: cmd, topic: (topicEl.value || 'memory').trim()}, extra||{});
    ws && ws.readyState === 1 && ws.send(JSON.stringify(payload));
  }

  async function videoMode(){
    // 1-click flow for Devpost recording:
    // run scenario -> refresh alerts -> refresh news -> refresh cases
    log({type:'video_mode', step:'start'});
    send('run_memory_burst');
    setStatus('alertsStatus', 'Waiting for scenario…', 'warn');
    setStatus('newsStatus', 'Waiting for scenario…', 'warn');
    setStatus('casesStatus', 'Waiting for scenario…', 'warn');

    // give backend a moment to write rows
    await new Promise(r => setTimeout(r, 900));
    await refreshAlerts();
    await refreshNews();
    await refreshCases();
    log({type:'video_mode', step:'done'});
  }

  document.getElementById('btnBurst').onclick = () => send('run_memory_burst');
  document.getElementById('btnNews').onclick = () => refreshNews();
  document.getElementById('btnAlerts').onclick = () => refreshAlerts();
  document.getElementById('btnCases').onclick = () => refreshCases();
  document.getElementById('btnVideo').onclick = () => videoMode();


  if(btnSend){
    btnSend.onclick = () => {
      const t = (promptEl && promptEl.value || '').trim();
      if(!t) return;
      appendChat('user', t);
      ws && ws.readyState === 1 && ws.send(JSON.stringify({type:'text', text:t}));
      if(promptEl) promptEl.value = '';
    };
  }
  if(promptEl){
    promptEl.addEventListener('keydown', (e) => {
      if(e.key === 'Enter'){
        e.preventDefault();
        btnSend && btnSend.click();
      }
    });
  }

  // initial paint
  refreshCases();
  refreshAlerts();
  refreshNews();
  renderGrounded(null);
})();
