(function(){
  const out = document.getElementById('out');
  const conn = document.getElementById('conn');
  const topicEl = document.getElementById('topic');

  const wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host.replace(':8080', ':8081') + '/ws';
  document.getElementById('wsUrl').textContent = wsUrl;

  function log(obj){
    const s = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
    out.textContent = s + "\n\n" + out.textContent;
  }

  let ws;
  function connect(){
    ws = new WebSocket(wsUrl);
    ws.onopen = () => { conn.textContent = 'WS: connected'; log({type:'system', message:'connected'}); };
    ws.onclose = () => { conn.textContent = 'WS: disconnected'; setTimeout(connect, 1000); };
    ws.onerror = (e) => { log({type:'error', message:'ws error', e: String(e)}); };
    ws.onmessage = (ev) => {
      try { log(JSON.parse(ev.data)); } catch { log(ev.data); }
    };
  }
  connect();

  function send(cmd, extra){
    const payload = Object.assign({type:'command', command: cmd, topic: topicEl.value || 'memory'}, extra||{});
    ws && ws.readyState === 1 && ws.send(JSON.stringify(payload));
  }

  document.getElementById('btnBurst').onclick = () => send('run_memory_burst');
  document.getElementById('btnNews').onclick = () => send('list_news');
  document.getElementById('btnAlerts').onclick = () => send('list_alerts');
})();
