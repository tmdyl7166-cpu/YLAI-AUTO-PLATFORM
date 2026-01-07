// stripped page controller
void 0;
// deprecated file: monitor-inline.js (not referenced)
// Deprecated: use /static/js/pages/monitor.js
(function(){
  try { console.warn('[deprecated] monitor-inline.js is not used anymore.'); } catch {}
})();

  // Placeholder modules + merge from backend
  let modules = [
    { api: "/api/task1", script: "task1.py", module: "数据采集", desc: "采集接口数据", progress: 40 },
    { api: "/api/task2", script: "task2.py", module: "AI推理", desc: "执行模型推理", progress: 0 }
  ];
  async function loadModulesFromBackend(){
    try{
      const mod = await import('/static/js/modules.js');
      const names = await mod.apiModules();
      if(Array.isArray(names)){
        const merged = names.map(n => ({ api: `/api/${n}`, script: `${n}.py`, module: n, desc: `后端脚本 ${n}`, progress: 0 }));
        const byName = new Map(merged.map(m => [m.module, m]));
        modules.forEach(m => { if(!byName.has(m.module)) byName.set(m.module, m); });
        modules = Array.from(byName.values());
      }
    }catch(e){ /* 保留本地占位 */ }
  }

  // Logs + SSE fallback
  let logs = ["["+new Date().toLocaleTimeString()+"] 系统启动"];
  let logSSE = null;
  function startLogSSE(){
    try{
      if (logSSE) { logSSE.close(); logSSE = null; }
      const base = (window.MON_CONFIG && MON_CONFIG.apiBase) || '/api';
      const url = String(base).replace(/\/$/, '') + '/sse/logs';
      logSSE = new EventSource(url);
      logSSE.onmessage = (ev) => {
        if (ev && ev.data) {
          try {
            const payload = JSON.parse(ev.data);
            if (Array.isArray(payload.lines)) {
              logs = logs.concat(payload.lines).slice(-1000);
              renderLogsBox();
            }
          } catch {
            logs.push(ev.data);
            renderLogsBox();
          }
        }
      };
      logSSE.onerror = () => { if (logSSE) { logSSE.close(); logSSE = null; } };
    }catch(e){ /* ignore */ }
  }
  function renderLogsBox(){
    const logBox = document.getElementById("logBox");
    const filterEl = document.getElementById("logFilter");
    const filter = (filterEl && filterEl.value || '').trim().toLowerCase();
    let filtered = logs;
    if (filter) filtered = logs.filter(l => l.toLowerCase().includes(filter));
    if(logBox) logBox.innerText = filtered.join("\n");
  }

  // WS monitor: /ws/monitor
  let wsMon = null;
  function startWSMonitor(){
    try{
      if(wsMon){ wsMon.close(); wsMon = null; }
      const base = (window.MON_CONFIG && MON_CONFIG.wsBase) || '';
      const url = (base ? base.replace(/\/$/,'') : '') + '/ws/monitor';
      wsMon = new WebSocket((url.startsWith('ws')?url:((location.protocol==='https:'?'wss':'ws')+'://'+location.host+url)));
      wsMon.onmessage = (ev)=>{
        try{
          const evt = JSON.parse(ev.data);
          const line = `[${evt.level||'INFO'}] ${evt.name||'event'} | ${evt.message||''}`;
          logs.push(line);
          if(evt.layer){
            const id = 'layer-'+String(evt.layer).toLowerCase();
            const el = document.getElementById(id);
            if(el){
              if(evt.error){ el.dataset.error = '1'; el.classList.add('has-error'); }
              if(typeof evt.elapsed_ms === 'number'){ el.dataset.elapsed = String(evt.elapsed_ms); }
              el.querySelector('.layer-output')?.textContent = evt.message || '';
            }
          }
          renderLogsBox();
        }catch(e){ logs.push(String(ev.data||'')); renderLogsBox(); }
      };
    }catch(e){ /* 忽略 */ }
  }

  // Render placeholders table
  function renderPlaceholders(){
    const tbody = document.getElementById("placeholderTable");
    if(!tbody) return;
    tbody.innerHTML = "";
    fetch('/pages/data/crawler_status.json?t=' + Date.now()).then(r => r.ok ? r.json() : null).then(status => {
      const runningScript = status && status.running && status.script ? status.script : null;
      return fetch('/pages/未完成内容.md?t=' + Date.now()).then(r => r.ok ? r.text() : Promise.reject('load md failed')).then(md => ({ md, runningScript }));
    }).then(({ md, runningScript }) => {
      const lines = md.split(/\n/);
      const items = [];
      let currentGroup = '';
      lines.forEach(line => {
        const groupMatch = line.match(/^##\s+(.+?)\s*$/);
        if (groupMatch) { currentGroup = groupMatch[1]; return; }
        const itemMatch = line.match(/^\s*-\s*\[(x|X|\s)\]\s*(GET|POST|DELETE)\s+`([^`]+)`\s*(?:→\s*(.+))?$/i);
        if (itemMatch) {
          const checked = String(itemMatch[1]).toLowerCase() === 'x';
          const method = itemMatch[2].toUpperCase();
          const path = itemMatch[3];
          const desc = (itemMatch[4] || '').replace(/`/g, '').trim();
          items.push({ api: `${method} ${path}`, script: '-', module: currentGroup || '-', desc: desc || '—', progress: checked ? 100 : 0 });
        }
      });
      const rows = items.length ? items : modules.map(m => ({ api: m.api, script: m.script, module: m.module, desc: m.desc, progress: m.progress }));
      rows.forEach(m => {
        const tr = document.createElement('tr');
        const scriptDisplay = (m.progress < 100) ? (m.module || '-') : (runningScript || m.script || '-');
        tr.innerHTML = `<td>${m.api}</td><td>${scriptDisplay}</td><td>${m.module}</td><td>${m.desc}</td><td>${m.progress}%</td>`;
        tbody.appendChild(tr);
      });
    }).catch(() => {
      modules.forEach(m => {
        const tr = document.createElement('tr');
        const scriptDisplay = (m.progress < 100) ? (m.module || '-') : (m.script || '-');
        tr.innerHTML = `<td>${m.api}</td><td>${scriptDisplay}</td><td>${m.module}</td><td>${m.desc}</td><td>${m.progress}%</td>`;
        tbody.appendChild(tr);
      });
    });
  }

  // Executed scripts list + AI optimize panel
  function wireAIOptimizePanel(){
    const input = document.getElementById('aiErrorInputMon');
    const btn = document.getElementById('aiOptimizeSubmitMon');
    const clr = document.getElementById('aiOptimizeClearMon');
    const out = document.getElementById('aiOptimizeResultMon');
    function render(obj){ try{ const data=(obj&&obj.data&&obj.data.data)?obj.data.data:(obj&&obj.data?obj.data:obj); out.textContent = (data && data.status==='success') ? JSON.stringify(data.data, null, 2) : JSON.stringify(obj, null, 2);}catch(e){ out.textContent=String(e);} }
    btn?.addEventListener('click', async ()=>{ const text=input.value||''; if(!text){ out.textContent='请先粘贴错误文本。'; return;} btn.disabled=true; out.textContent='提交中...'; try{ const res= await (window.AI && window.AI.optimizeError ? window.AI.optimizeError(text,{page:'monitor.html'}) : Promise.resolve({code:1,error:'AI helper missing'})); render(res);}catch(err){ out.textContent=String(err);} btn.disabled=false; });
    clr?.addEventListener('click', ()=>{ input.value=''; out.textContent=''; });
  }

  // Charts (ECharts)
  function initCharts(){
    if(!window.echarts){ setTimeout(initCharts, 200); return; }
    let chartDom = document.getElementById('deploymentChart');
    if(!chartDom) return;
    let myChart = echarts.init(chartDom);
    let chartOption = { title: { text: '部署进度与资源', textStyle: { color: '#1de9b6' } }, tooltip: { trigger: 'axis' }, grid: [ { left: '8%', top: 40, width: '40%', height: '70%' }, { right: '6%', top: 40, width: '40%', height: '70%' } ], xAxis: [ { gridIndex: 0, type: 'category', data: modules.map(m => m.module), axisLine: { lineStyle: { color: '#1de9b6' } } }, { gridIndex: 1, type: 'category', data: [], axisLine: { lineStyle: { color: '#1de9b6' } } } ], yAxis: [ { gridIndex: 0, type: 'value', name: '进度%', axisLine: { lineStyle: { color: '#1de9b6' } } }, { gridIndex: 1, type: 'value', name: '资源%', axisLine: { lineStyle: { color: '#1de9b6' } } } ], series: [ { name: '进度%', type: 'bar', xAxisIndex: 0, yAxisIndex: 0, data: modules.map(m => m.progress), itemStyle: { color: '#1de9b6' } }, { name: 'CPU%', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: [], smooth: true, lineStyle: { color: '#ff9800' } }, { name: 'MEM%', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: [], smooth: true, lineStyle: { color: '#03a9f4' } } ] };
    myChart.setOption(chartOption);
    window.__MON_CHART__ = { myChart, chartOption };
  }
  const cpuSeriesData = []; const memSeriesData = []; const tsLabels = [];
  function updateChart(){ const ctx = window.__MON_CHART__; if(!ctx) return; const { myChart, chartOption } = ctx; chartOption.xAxis[0].data = modules.map(m => m.module); chartOption.series[0].data = modules.map(m => m.progress); chartOption.xAxis[1].data = tsLabels; chartOption.series[1].data = cpuSeriesData.map(p => p.v); chartOption.series[2].data = memSeriesData.map(p => p.v); myChart.setOption(chartOption); }

  async function updateProgress(){
    try{
      const resp = await fetch('/pages/data/stats.json?t=' + Date.now());
      if(resp.ok){ const stats = await resp.json(); if(stats && stats.modules && Array.isArray(stats.modules)){ const modMap = new Map(modules.map(m => [m.module, m])); stats.modules.forEach(sm => { const m = modMap.get(sm.name); if(m){ m.progress = typeof sm.progress === 'number' ? sm.progress : m.progress; m.status = sm.status || m.status; } }); } if(stats && stats.series){ if (Array.isArray(stats.series.cpu)) { cpuSeriesData.length = 0; tsLabels.length = 0; stats.series.cpu.forEach(p => { cpuSeriesData.push(p); const ts = Number(p.t || 0); const d = new Date(ts * 1000); tsLabels.push(isFinite(d.getTime()) ? `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}` : ''); }); } if (Array.isArray(stats.series.mem)) { memSeriesData.length = 0; stats.series.mem.forEach(p => memSeriesData.push(p)); } } }
    }catch(e){ modules.forEach(m => { if (m.progress < 100) { m.progress += Math.floor(Math.random() * 10); if (m.progress > 100) m.progress = 100; logs.push(`[${new Date().toLocaleTimeString()}] 模块 ${m.module} 进度更新: ${m.progress}%`); } }); }
  }

  function renderExecutedScripts(){ const ul = document.getElementById("executedScripts"); if(!ul) return; ul.innerHTML = ""; fetch('/pages/data/crawler_status.json?t=' + Date.now()).then(r => r.ok ? r.json() : null).then(st => { const list = new Set([]); if (st && st.running && st.script) list.add(st.script); Array.from(list).forEach(s => { const li = document.createElement('li'); li.textContent = s; ul.appendChild(li); }); }).catch(() => { /* ignore */ }); }

  function renderScriptList(){ const ul = document.getElementById("scriptList"); if(!ul) return; const filterEl = document.getElementById("scriptFilter"); const filter = (filterEl && filterEl.value || '').trim().toLowerCase(); Array.from(ul.children).forEach(li => { if (li.textContent.toLowerCase().includes(filter)) { li.style.display = ""; } else li.style.display = "none"; li.onclick = () => { const selectedScript = li.dataset.script; logs.push(`[${new Date().toLocaleTimeString()}] 选中脚本: ${selectedScript}`); renderLogsBox(); }; }); }

  async function startScript(){ const filterEl = document.getElementById("scriptFilter"); const ul = document.getElementById("scriptList"); const selected = (ul && ul.querySelector('li[data-script]') ? ul.querySelector('li[data-script]').dataset.script : null); if(!selected) return window.Toast && window.Toast.show ? window.Toast.show("请先选择脚本", "warn") : alert('请先选择脚本'); const time = Number(document.getElementById("pollingTime").value || 3); const path = document.getElementById("pathInput").value || '/data/tasks'; try { const resp = await apiFetch('/crawler/start', { method: 'POST', body: JSON.stringify({ script: selected, interval: time, path }) }); const text = await resp.text(); logs.push(`[${new Date().toLocaleTimeString()}] 启动脚本: ${selected} | 响应: ${text}`); } catch (e) { logs.push(`[${new Date().toLocaleTimeString()}] 启动失败: ${String(e)}`); } renderLogsBox(); }

  function updateUI(){ loadModulesFromBackend(); updateProgress(); renderPlaceholders(); renderLogsBox(); renderExecutedScripts(); renderScriptList(); updateChart(); }
  setInterval(updateUI, 3000); updateUI(); startLogSSE(); startWSMonitor(); wireAIOptimizePanel(); initCharts();
})();
