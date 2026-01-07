// SPA 路由系统 with lazy loading
const routes = {
  home: () => `<section><h2>夜灵多功能检测仪</h2><ul><li>脚本运行：通过统一 API 触发后端内核脚本执行，支持参数化。</li><li>系统监控：实时 WebSocket 事件与日志，展示运行状态。</li><li>API 文档：常用接口说明与示例，便于联调与测试。</li><li>管线编排：结构化任务编排与状态回传，支持 DAG。</li><li>AI 代理演示：自然语言转任务，联动管线执行与结果呈现。</li></ul></section>`,
  run: async () => `<iframe src="/pages/run.html" style="width:100%; height:600px; border:none;"></iframe>`,
  monitor: async () => `<iframe src="/pages/monitor.html" style="width:100%; height:600px; border:none;"></iframe>`,
  'api-doc': async () => `<iframe src="/pages/api-doc.html" style="width:100%; height:600px; border:none;"></iframe>`,
  'visual-pipeline': async () => `<iframe src="/pages/visual_pipeline.html" style="width:100%; height:600px; border:none;"></iframe>`,
  rbac: async () => `<iframe src="/pages/rbac.html" style="width:100%; height:600px; border:none;"></iframe>`,
  'ai-demo': async () => `<iframe src="/pages/ai-demo.html" style="width:100%; height:600px; border:none;"></iframe>`
};

async function loadRoute(route) {
  const root = document.getElementById('index-root');
  const content = routes[route] || routes.home();
  root.innerHTML = typeof content === 'string' ? content : await content();
}

window.addEventListener('hashchange', () => {
  const route = location.hash.slice(1) || 'home';
  loadRoute(route);
});

// stripped page controller
void 0;
// 页面初始化时，如存在项目状态容器则渲染

document.addEventListener('DOMContentLoaded', async () => {
  loadRoute(location.hash.slice(1) || 'home');

  // 导航点击事件
  document.getElementById('main-nav').addEventListener('click', (e) => {
    if (e.target.tagName === 'A') {
      e.preventDefault();
      const route = e.target.getAttribute('data-route');
      location.hash = route;
    }
  });

  // Minimal clickable module placeholder guard
  (function ensureMinimal(){
    const root = document.getElementById('index-root');
    if (root && !root.children.length) {
      const section = document.createElement('section');
      section.className = 'card';
      const btn = document.createElement('button');
      btn.className = 'btn';
      btn.textContent = '打开模块列表';
      btn.onclick = ()=> alert('模块列表占位（后续由模块渲染）');
      section.appendChild(btn);
      root.appendChild(section);
    }
  })();
  // 顶级容器
  const root = document.getElementById('ylai-root');
  if (!root) return;
  // 渲染基础布局（顶栏交由 common/topbar.js 统一渲染）
  root.innerHTML = `
    <div class="layout-root">
      <div class="main">
        <aside class="side" id="sideBar" aria-label="侧边栏"></aside>
        <main class="main-content" id="main-content"></main>
      </div>
      <div class="footer">© 2025 夜灵多功能检测仪</div>
    </div>
  `;


  // 渲染侧边栏一二级下拉菜单
  const menuGroups = [
      {
        title: '任务中心',
        items: [
          {
            key: 'task-center',
            label: '任务中心',
            children: [
              { key: 'param_deploy', label: '参数部署' },
              { key: 'smart-schedule', label: '智能调度' },
              { key: 'collect-task', label: '采集任务' },
              { key: 'enum-task', label: '枚举任务' },
              { key: 'recognize-task', label: '识别任务' },
              { key: 'crack-task', label: '破解任务' },
              { key: 'status', label: '自动化状态' },
              { key: 'log', label: '日志管理' },
              { key: 'workflow-deploy', label: '工作流部署' }
            ]
          }
        ]
      },
    {
      title: '高级功能',
      items: [
        {
          key: 'advanced',
          label: '高级功能',
          children: [
            { key: 'ai-advanced', label: 'AI高级联动' },
            { key: 'cross-parse', label: '交叉解析' },
            { key: 'anti-trace', label: '反追反穿' },
            { key: 'extreme-break', label: '极限突破' },
            { key: 'decode-challenge', label: '破译挑战' }
          ]
        }
      ]
    },
    {
      title: '系统设置',
      items: [
        {
          key: 'settings',
          label: '系统设置',
          children: [
            { key: 'auth', label: '权限管理' },
            { key: 'api-doc', label: 'API接口文档' },
            { key: 'prod-control', label: '后端控制' },
            { key: 'ai-train', label: 'AI训练' },
            { key: 'fastapi-control', label: 'FastAPI服务联动' }
          ]
        }
      ]
    },
    {
      title: '增强监控',
      items: [
        {
          key: 'monitor-group',
          label: '增强监控',
          children: [
            { key: 'monitor', label: '增强监控', link: '/pages/monitor.html' }
          ]
        }
      ]
    }
  ];
  const sideBar = document.getElementById('sideBar');
  if (sideBar) {
    let html = '';
    menuGroups.forEach((group, gi) => {
      html += `<li class="menu-group">
        <div class="menu-group-title collapsible" data-group="${gi}">${group.title}</div>
        <ul class="menu-sub" style="max-height:0;opacity:0;">`;
      group.items.forEach((item, ii) => {
        if (item.children) {
          // 一级菜单下所有二级项
          item.children.forEach(child => {
            if (child.link) {
              html += `<li><a href="${child.link}" class="menu-item menu-item2" data-module="${child.key}">${child.label}</a></li>`;
            } else {
              html += `<li><a href="#" class="menu-item menu-item2" data-module="${child.key}">${child.label}</a></li>`;
            }
          });
        }
      });
      html += '</ul></li>';
    });
    sideBar.innerHTML = `<section class="side-inner"><ul class="menu">${html}</ul></section>`;
    // 一级菜单点击收缩/展开二级菜单（带动画，修复初始样式）
    sideBar.querySelectorAll('.menu-group-title.collapsible').forEach((title, idx) => {
      const sub = title.parentElement.querySelector('.menu-sub');
      if(idx===0 && sub){
        sub.classList.add('open');
        title.classList.add('open');
        sub.style.maxHeight = sub.scrollHeight + 'px';
        sub.style.opacity = '1';
      }
      title.addEventListener('click', () => {
        if(sub){
          const isOpen = sub.classList.contains('open');
          if(isOpen){
            sub.classList.remove('open');
            title.classList.remove('open');
            sub.style.maxHeight = '0';
            sub.style.opacity = '0';
          }else{
            sub.classList.add('open');
            title.classList.add('open');
            sub.style.maxHeight = sub.scrollHeight + 'px';
            sub.style.opacity = '1';
          }
        }
      });
    });
    // 自动绑定所有菜单项点击事件，确保联动
    bindMenuEvents();

  }

// 菜单事件绑定函数，确保每次菜单渲染后都能正常联动
function bindMenuEvents() {
  document.querySelectorAll('.menu-item[data-module]').forEach(item => {
    item.onclick = function(e) {
      e.preventDefault();
      const key = item.getAttribute('data-module');
      renderModuleContent(key);
      document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const main = document.getElementById('main-content');
      if(main) main.scrollTo({top:0,behavior:'smooth'});
    };
  });
}

// 渲染仪表盘区块
if (sideBar) {
    const dashboard = `<section class="dashboard" aria-label="仪表盘">
      <div class="dashboard-box"><div style="font-size:12px;color:#667eea;font-weight:600;">任务总数</div><div id="task-stats-total2" style="font-size:18px;color:#42e695;font-weight:700;line-height:1.2;">-</div></div>
      <div class="dashboard-box"><div style="font-size:12px;color:#667eea;font-weight:600;">已完成</div><div id="task-stats-done2" style="font-size:18px;color:#667eea;font-weight:700;line-height:1.2;">-</div></div>
      <div class="dashboard-box" style="margin-bottom:0;"><div style="font-size:12px;color:#667eea;font-weight:600;">进度</div><div style="height:14px;display:flex;align-items:center;justify-content:center;"><div style="background:#e0eafc;border-radius:8px;width:44px;height:8px;position:relative;overflow:hidden;"><div id="task-progress-bar2" style="background:linear-gradient(90deg,#42e695 0%,#667eea 100%);height:100%;width:0%;transition:width 0.5s;"></div></div><span id="task-progress-text2" style="font-size:11px;color:#764ba2;margin-left:4px;">0%</span></div></div>
    </section>`;
    sideBar.insertAdjacentHTML('afterbegin', dashboard);
  }

  // 渲染主内容区块（统一从 modules 注册表装配）
  try {
    const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__');
    await mountModule('index', 'ylai-root');
  } catch (e) {
    // 回退到现有渲染逻辑，保证不破坏现状
    renderMainContent();
  }

  // 用户徽标渲染
  (async function(){
    try{ const mod=await import('/static/js/auth.js'); const role=localStorage.getItem('yl_user_role')||'user'; const wrap=document.getElementById('user-badge'); if(!wrap) return; wrap.innerHTML = `<span style="padding:6px 10px;border-radius:999px;font-size:12px;background:#0a0f1e;color:#1de9b6;border:1px solid rgba(29,240,255,0.35);">${role}</span>`; }catch(_){ }
  })();

  // ...菜单事件绑定已由 bindMenuEvents() 自动处理...
  try{ const rootEl = document.getElementById('ylai-root'); if(rootEl){ rootEl.style.opacity = '1'; } }catch(_){ }
});

// 主内容区块渲染（默认首页/模块切换）

// 单模块内容渲染（菜单切换）
function renderModuleContent(key) {
  const main = document.getElementById('main-content');
  if (!main) return;
  main.innerHTML = '';
  // 根据 key 渲染不同模块内容
  const renderer = MODULE_RENDERERS[key];
  if (renderer) {
    renderer(main);
  } else {
    main.appendChild(card({
      title: `模块：${key}`,
      note: '此处可扩展具体业务逻辑与UI。',
      content: `<div class="placeholder">${key} 功能区块，待 JS 实现具体逻辑。</div>`
    }));
  }
}


// 版本打印与模块事件监听
(function(){
  try{
    import('/static/js/modules.js').then(mod=>{ try{ mod.printVersion && mod.printVersion(); }catch(_){} });
  }catch(_){}
  window.addEventListener('modules:invoke', (e)=>{ console.debug('[index] invoke', e.detail); }, { passive:true });
})();

// 通用工具：鉴权头与统一请求
async function getAuthHeaders(){
  try { const mod = await import('/static/js/auth.js'); return mod.auth?.getAuthHeaders?.() || {}; } catch(_) { return {}; }
}
async function api(path, init={}){
  const headers = Object.assign({}, init.headers||{}, await getAuthHeaders());
  const resp = await fetch(path, Object.assign({}, init, { headers }));
  const ct = resp.headers.get('content-type')||'';
  const data = ct.includes('application/json') ? await resp.json() : await resp.text();
  return { ok: resp.ok, status: resp.status, data };
}

// 模块渲染器
const MODULE_RENDERERS = {
  // 参数部署
  'param_deploy': (root)=>{
    root.appendChild(card({ title:'参数部署', note:'统一参数编辑、校验与下发；支持导入导出与版本化。' }));
    const box = document.createElement('div');
    box.className = 'card';
    box.innerHTML = `
      <div class="card-title">参数表单</div>
      <div class="card-note">版本/并发/深度/超时、UA、代理、目标分级、风控关键词</div>
      <div class="btn-row" style="margin-top:8px">
        <button id="p-validate" class="btn">参数校验</button>
        <button id="p-save" class="btn">保存/下发</button>
        <button id="p-load" class="btn">加载</button>
        <button id="p-export" class="btn">导出</button>
        <button id="p-import" class="btn">导入</button>
        <button id="p-sort" class="btn">排序预览</button>
        <button id="p-visibility" class="btn">可见性枚举</button>
        <button id="p-risk" class="btn">风控识别</button>
        <button id="p-health" class="btn">服务健康</button>
        <button id="p-events" class="btn">事件联动</button>
      </div>
      <pre id="p-result" class="placeholder" style="margin-top:10px; white-space:pre-wrap"></pre>
    `;
    root.appendChild(box);
    const r = box.querySelector('#p-result');
    box.querySelector('#p-validate').onclick = async()=>{ const res = await api('/api/config/validate',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-save').onclick = async()=>{ const res = await api('/api/config/save',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-load').onclick = async()=>{ const res = await api('/api/config/load'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-export').onclick = async()=>{ const res = await api('/api/config/get'); r.textContent = typeof res.data==='string'?res.data:JSON.stringify(res, null, 2); };
    box.querySelector('#p-import').onclick = async()=>{ const res = await api('/api/config/save',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-sort').onclick = async()=>{ const res = await api('/api/config/ranking/preview',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-visibility').onclick = async()=>{ const res = await api('/api/config/visibility/options'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-risk').onclick = async()=>{ const res = await api('/api/placeholder/risk'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-health').onclick = async()=>{ const res = await api('/health'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#p-events').onclick = async()=>{ const res = await api('/api/events/trigger',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({kind:'config-change'})}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 智能调度
  'smart-schedule': (root)=>{
    root.appendChild(card({ title:'智能调度', note:'调度器启停、优先级与限流策略；支持重试与失败转移。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="s-start" class="btn">启动调度器</button>
        <button id="s-stop" class="btn">停止调度器</button>
        <button id="s-status" class="btn">状态</button>
        <button id="s-ai-register" class="btn">AI服务注册</button>
        <button id="s-ai-compose" class="btn">AI联动编排</button>
        <button id="s-exec-async" class="btn">脚本异步执行</button>
        <button id="s-fallback" class="btn">失败回退策略</button>
      </div>
      <pre id="s-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#s-result');
    box.querySelector('#s-start').onclick = async()=>{ const res = await api('/api/scheduler/start',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-stop').onclick = async()=>{ const res = await api('/api/scheduler/stop'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-status').onclick = async()=>{ const res = await api('/api/scheduler/status'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-ai-register').onclick = async()=>{ const res = await api('/api/ai/register',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({model:'qwen2.5', route:'/api/ai'})}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-ai-compose').onclick = async()=>{ const res = await api('/api/ai/compose',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pipeline:['recognize','classify','plan']})}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-exec-async').onclick = async()=>{ const res = await api('/api/scripts/exec-async',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({script:'demo', params:{}})}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#s-fallback').onclick = async()=>{ const res = await api('/api/scheduler/fallback',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({policy:'record-and-retry'})}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 采集任务
  'collect-task': (root)=>{
    root.appendChild(card({ title:'采集任务', note:'创建、批量导入、实时进度与失败重试。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="c-list" class="btn">任务列表</button>
        <button id="c-create" class="btn">创建任务</button>
        <button id="c-validate" class="btn">表单校验</button>
        <button id="c-detail" class="btn">任务详情</button>
        <button id="c-start" class="btn">启动任务</button>
        <button id="c-stop" class="btn">停止任务</button>
      </div>
      <pre id="c-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#c-result');
    box.querySelector('#c-list').onclick = async()=>{ const res = await api('/api/collect/tasks'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#c-create').onclick = async()=>{ const res = await api('/api/collect/tasks/create',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#c-validate').onclick = async()=>{ const form = new FormData(); form.append('keyword','测试'); const res = await fetch('/api/collect/validate',{method:'POST', body: form}); const data = await res.json().catch(()=>({})); r.textContent = JSON.stringify({ok:res.ok,status:res.status,data}, null, 2); };
    box.querySelector('#c-detail').onclick = async()=>{ const res = await api('/api/collect/tasks/detail',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:'task-001'})}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#c-start').onclick = async()=>{ const res = await api('/api/collect/tasks/start',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:'task-001'})}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#c-stop').onclick = async()=>{ const res = await api('/api/collect/tasks/stop',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:'task-001'})}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 枚举任务
  'enum-task': (root)=>{
    root.appendChild(card({ title:'枚举任务', note:'字典/规则驱动的枚举扫描与结果采集。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="e-list" class="btn">任务列表</button>
        <button id="e-scan" class="btn">触发扫描</button>
        <button id="e-bin" class="btn">银行卡BIN校验</button>
        <button id="e-gamecard" class="btn">游戏卡枚举</button>
        <button id="e-virtualcard" class="btn">虚拟卡枚举</button>
        <button id="e-mnemonic" class="btn">助记词枚举</button>
        <button id="e-hexkey" class="btn">十六进制密钥</button>
        <button id="e-key32" class="btn">32位密钥</button>
        <button id="e-config" class="btn">属性/关键词配置</button>
        <button id="e-cross" class="btn">交叉联动</button>
      </div>
      <pre id="e-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#e-result');
    box.querySelector('#e-list').onclick = async()=>{ const res = await api('/api/enum/tasks'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-scan').onclick = async()=>{ const res = await api('/api/enum/tasks/scan',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-bin').onclick = async()=>{ const res = await api('/api/enum/bin/check',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-gamecard').onclick = async()=>{ const res = await api('/api/enum/gamecard/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-virtualcard').onclick = async()=>{ const res = await api('/api/enum/virtualcard/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-mnemonic').onclick = async()=>{ const res = await api('/api/enum/mnemonic/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-hexkey').onclick = async()=>{ const res = await api('/api/enum/hexkey/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-key32').onclick = async()=>{ const res = await api('/api/enum/key32/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-config').onclick = async()=>{ const res = await api('/api/enum/config/save',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#e-cross').onclick = async()=>{ const res = await api('/api/enum/cross/run',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 识别任务
  'recognize-task': (root)=>{
    root.appendChild(card({ title:'识别任务', note:'内容识别/OCR/分类等识别流程提交与跟踪。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="r-submit" class="btn">提交识别任务</button>
        <button id="r-status" class="btn">识别状态</button>
        <button id="r-trace" class="btn">路由追踪</button>
        <button id="r-dns" class="btn">DNS/ASN</button>
        <button id="r-entities" class="btn">组织/实体</button>
        <button id="r-social" class="btn">社交聚合</button>
        <button id="r-coop" class="btn">跨模块协同</button>
        <button id="r-apphints" class="btn">软件线索</button>
      </div>
      <pre id="r-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#r-result');
    box.querySelector('#r-submit').onclick = async()=>{ const res = await api('/api/recognize/tasks/create',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-status').onclick = async()=>{ const res = await api('/api/recognize/tasks/status',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-trace').onclick = async()=>{ const res = await api('/api/recognize/trace',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-dns').onclick = async()=>{ const res = await api('/api/recognize/dns_asn',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-entities').onclick = async()=>{ const res = await api('/api/recognize/entities',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-social').onclick = async()=>{ const res = await api('/api/recognize/social',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-coop').onclick = async()=>{ const res = await api('/api/recognize/coop',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#r-apphints').onclick = async()=>{ const res = await api('/api/recognize/app_hints',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 破解任务
  'crack-task': (root)=>{
    root.appendChild(card({ title:'破解任务', note:'口令/验证码等破解任务编排与执行监控。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="k-start" class="btn">启动破解任务</button>
        <button id="k-status" class="btn">任务状态</button>
        <button id="k-captcha" class="btn">验证码破解</button>
        <button id="k-urlcodec" class="btn">URL编码解码</button>
        <button id="k-parse" class="btn">解析渗透</button>
        <button id="k-html" class="btn">网页解析</button>
        <button id="k-unzip" class="btn">zip解锁</button>
        <button id="k-account" class="btn">账号密码逻辑</button>
        <button id="k-bypass" class="btn">安全防控破解</button>
        <button id="k-android" class="btn">安卓密码破解</button>
        <button id="k-gphotos" class="btn">谷歌相册破解</button>
        <button id="k-card" class="btn">银行卡校验</button>
        <button id="k-b64" class="btn">B64解码</button>
        <button id="k-denoise" class="btn">打码清除</button>
      </div>
      <pre id="k-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#k-result');
    box.querySelector('#k-start').onclick = async()=>{ const res = await api('/api/crack/start',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-status').onclick = async()=>{ const res = await api('/api/crack/status',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-captcha').onclick = async()=>{ const res = await api('/api/crack/captcha',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-urlcodec').onclick = async()=>{ const res = await api('/api/crack/urlcodec',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-parse').onclick = async()=>{ const res = await api('/api/crack/parse',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-html').onclick = async()=>{ const res = await api('/api/crack/html',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-unzip').onclick = async()=>{ const res = await api('/api/crack/unzip',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-account').onclick = async()=>{ const res = await api('/api/crack/account',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-bypass').onclick = async()=>{ const res = await api('/api/crack/sec_bypass',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-android').onclick = async()=>{ const res = await api('/api/crack/android',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-gphotos').onclick = async()=>{ const res = await api('/api/crack/google_photos',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-card').onclick = async()=>{ const res = await api('/api/crack/card_check',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-b64').onclick = async()=>{ const res = await api('/api/crack/b64',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#k-denoise').onclick = async()=>{ const res = await api('/api/crack/denoise',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 自动化状态
  'status': (root)=>{
    root.appendChild(card({ title:'自动化状态', note:'实时监控各模块状态与进度。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="a-overview" class="btn">运行总况</button>
        <button id="a-progress" class="btn">进度聚合</button>
        <button id="a-security" class="btn">安全级别</button>
      </div>
      <div class="chart-grid" style="margin-top:10px">
        <div class="chart-box">
          <div class="title">进度曲线</div>
          <canvas id="chart-line" class="chart-canvas"></canvas>
        </div>
        <div class="chart-box">
          <div class="title">K线占位</div>
          <canvas id="chart-k" class="chart-canvas"></canvas>
        </div>
      </div>
      <pre id="a-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#a-result');
    box.querySelector('#a-overview').onclick = async()=>{ const res = await api('/api/status'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#a-progress').onclick = async()=>{ const res = await api('/api/scheduler/status'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#a-security').onclick = async()=>{ const res = await api('/api/risk/inspect', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})}); r.textContent = JSON.stringify(res, null, 2); };
    // 懒加载小型图表并渲染占位数据（若有接口则优先用接口数据）
    (async()=>{
      try{
        const mod = await import('/static/js/components/chart-mini.js');
        const lc = box.querySelector('#chart-line');
        const kc = box.querySelector('#chart-k');
        // 获取进度数据
        let progress = Array.from({length: 40}, (_,i)=> i ? Math.max(0, Math.min(100, Math.random()*20 + (i>0?0:0))) : Math.random()*10);
        try{
          const res = await api('/api/scheduler/status');
          const arr = (res.data && (res.data.points||res.data.progress||[])) || [];
          if(Array.isArray(arr) && arr.length>1) progress = arr.map(Number).filter(n=>Number.isFinite(n));
        }catch(_){ }
        mod.renderLineChart(lc, progress, {height: 180});
        // K线占位
        let candles = Array.from({length: 30}, (_,i)=>{
          const base = 100 + i*0.5 + (Math.sin(i/3)*5);
          const o = base + (Math.random()*4-2);
          const c = o + (Math.random()*6-3);
          const h = Math.max(o,c) + Math.random()*3;
          const l = Math.min(o,c) - Math.random()*3;
          return {t:i,o,h,l,c};
        });
        mod.renderCandleChart(kc, candles, {height: 180});
      }catch(e){ /* no-op */ }
    })();
  },

  // 日志管理
  'log': (root)=>{
    root.appendChild(card({ title:'日志管理', note:'查看、导出、清理系统运行日志。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="l-usage" class="btn">功能使用日志</button>
        <button id="l-clear" class="btn">清理日志</button>
      </div>
      <pre id="l-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#l-result');
    box.querySelector('#l-usage').onclick = async()=>{ const res = await api('/api/logs/usage'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#l-clear').onclick = async()=>{ const res = await api('/api/logs/clean',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
  },

  // 工作流部署
  'workflow-deploy': (root)=>{
    root.appendChild(card({ title:'工作流部署', note:'编排式工作流部署、版本管理与一键发布回滚。' }));
    const box = document.createElement('div'); box.className='card';
    box.innerHTML = `
      <div class="btn-row">
        <button id="w-list" class="btn">工作流列表</button>
        <button id="w-deploy" class="btn">部署/回滚</button>
      </div>
      <pre id="w-result" class="placeholder" style="margin-top:10px"></pre>`;
    root.appendChild(box);
    const r = box.querySelector('#w-result');
    box.querySelector('#w-list').onclick = async()=>{ const res = await api('/api/workflow/list'); r.textContent = JSON.stringify(res, null, 2); };
    box.querySelector('#w-deploy').onclick = async()=>{ const res = await api('/api/workflow/deploy',{method:'POST'}); r.textContent = JSON.stringify(res, null, 2); };
  }
};

// 全局健康指示器与内容区健康卡片
(function(){
  function init(){
    import('/static/js/health-widget.js').then(mod=>{
      const { initGlobalIndicator, initHealthCard } = mod;
      const stopIndicator = initGlobalIndicator({
        el: document.getElementById('global-health-indicator'),
        pollingMs: 5000
      });
      let stopCard;
      const hostCard = document.getElementById('health-card-host');
      if(hostCard){ stopCard = initHealthCard({ el: hostCard, pollingMs: 5000 }); }
      window.addEventListener('beforeunload', ()=>{ try{ stopIndicator&&stopIndicator(); stopCard&&stopCard(); }catch(_){} });
    }).catch(()=>{});
  }
  if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
// 健康状态检查与错误处理
async function updateHealth() {
  try {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('健康接口异常');
    const data = await res.json();
    const txtEl = document.getElementById('ghi-text');
    const dotEl = document.getElementById('ghi-dot');
    if (txtEl) txtEl.textContent = (data.data?.status) || (data.status) || 'OK';
    if (dotEl) dotEl.style.background = '#42e695';
  } catch (e) {
    const txtEl = document.getElementById('ghi-text');
    const dotEl = document.getElementById('ghi-dot');
    if (txtEl) txtEl.textContent = 'ERROR';
    if (dotEl) dotEl.style.background = '#ef4444';
  }
}

// 模块列表刷新与错误处理
async function updateModules() {
  try {
    // 统一带鉴权头
    const mod = await import('/static/js/auth.js').catch(()=>({auth:{getAuthHeaders:()=>({})}}));
    const res = await fetch('/api/modules', { headers: { ...mod.auth.getAuthHeaders?.() } });
    if (!res.ok) throw new Error('模块接口异常');
    const data = await res.json();
    const list = document.getElementById('modules-list');
    if (!list) return;
    list.innerHTML = '';
    (data.modules || []).forEach(m => {
      const li = document.createElement('li');
      li.textContent = m;
      list.appendChild(li);
    });
  } catch (e) {
    const list = document.getElementById('modules-list');
    if (list) list.innerHTML = '<li>加载失败</li>';
  }
}

// AI 提示提交与错误处理
async function submitPrompt() {
  const promptEl = document.getElementById('ai-prompt-input');
  const statusEl = document.getElementById('ai-result');
  if (!promptEl || !statusEl) return;
  const prompt = promptEl.value;
  statusEl.textContent = '处理中...';
  try {
    const mod = await import('/static/js/auth.js').catch(()=>({auth:{getAuthHeaders:()=>({})}}));
    const res = await fetch('/api/ai/pipeline', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', ...mod.auth.getAuthHeaders?.()},
      body: JSON.stringify({prompt})
    });
    if (!res.ok) throw new Error('AI接口异常');
    const data = await res.json();
    statusEl.textContent = (data.result) || (data.data?.output) || '无回复';
  } catch (e) {
    statusEl.textContent = 'AI请求失败';
  }
}

// DOM 渲染入口：根据容器 ID 构建卡片与控件
function renderMainContent() {
  const main = document.getElementById('main-content');
  if (!main) return;
  main.innerHTML = '';
  // 欢迎卡片
  main.appendChild(card({
    title: '欢迎',
    note: '此页面仅为 UI 框架的静态复制版本，用于新脚本的基础布局复用。'
  }));
  // AI 联动入口
  main.appendChild(card({
    title: '自然语言任务配置',
    note: '通过 /ai/pipeline 触发四模型联动',
    content: `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <input id="ai-prompt-input" placeholder="输入任务（中文）" style="flex:1;min-width:280px" />
      <button id="ai-run-btn" class="menu-item" style="background:#2563eb;color:#fff">运行 AI</button>
    </div>
    <pre id="ai-result" style="margin-top:8px;white-space:pre-wrap"></pre>`
  }));
  // 项目任务与部署状态
  main.appendChild(card({
    title: '项目任务与部署状态',
    note: '来自 PROJECT_STATUS.md（自动刷新需手动刷新页面）',
    content: `<div id="project-status"></div>`
  }));
  // 后端脚本模块
  main.appendChild(card({
    title: '后端脚本模块',
    note: '来源：优先 GET /scripts（兼容 /api/modules）',
    content: `<div id="modules-list" class="module-grid"></div>
      <div style="margin-top:8px;display:flex;gap:8px">
        <button id="btn-refresh-modules" class="menu-item" style="background:#2563eb;color:#fff">刷新脚本清单</button>
      </div>`
  }));
  // 快捷操作
  main.appendChild(card({
    title: '快捷操作',
    note: '常用端点快速验证',
    content: `<div style="display:flex;gap:8px;flex-wrap:wrap">
      <a class="menu-item" href="/pages/api-doc.html?action=health" style="background:#16a34a;color:#fff">健康检查 /health</a>
      <a class="menu-item" href="/pages/api-doc.html?action=scripts" style="background:#2563eb;color:#fff">脚本清单 /scripts</a>
      <a class="menu-item" href="/pages/api-doc.html?action=all" style="background:#7c3aed;color:#fff">全部探测</a>
    </div>`
  }));
  // 健康概览
  main.appendChild(card({
    title: '健康概览',
    note: '后端与AI延迟（含均值/P98）',
    content: `<div id="health-card-host"></div>`
  }));
}
function card({title, note, content}) {
  const div = document.createElement('div');
  div.className = 'card';
  if (title) {
    const t = document.createElement('div');
    t.className = 'card-title';
    t.textContent = title;
    div.appendChild(t);
  }
  if (note) {
    const n = document.createElement('div');
    n.className = 'card-note';
    n.textContent = note;
    div.appendChild(n);
  }
  if (content) {
    const c = document.createElement('div');
    c.innerHTML = content;
    div.appendChild(c);
  }
  return div;
}
// 页面初始化时渲染主内容
// 已在顶层初始化流程调用 renderMainContent，这里避免重复绑定

// 事件绑定与初始化
window.addEventListener('DOMContentLoaded', () => {
  updateHealth();
  updateModules();
  const aiBtn = document.getElementById('ai-run-btn');
  if (aiBtn) aiBtn.onclick = submitPrompt;
  const btnRefreshModules = document.getElementById('btn-refresh-modules');
  if (btnRefreshModules) btnRefreshModules.onclick = updateModules;
});

// 记录从首页跳转来源，供 api-doc 子站入口守卫使用
try{ sessionStorage.setItem('fromIndex', '1'); }catch(_){ }
