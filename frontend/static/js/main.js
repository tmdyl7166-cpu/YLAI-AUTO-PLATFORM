// stripped module (to be unified later)
void 0;
(function(global){
  // ---------- Config ----------
  const IndexConfig = (function(){
    const VERSION = '0.1.0-static';
    const MODULES = {
      'param_deploy':'参数部署','smart-schedule':'智能调度','collect-task':'采集任务','enum-task':'枚举任务','recognize-task':'识别任务','crack-task':'破解任务','status':'自动化状态','log':'日志管理','workflow-deploy':'工作流部署','ai-advanced':'AI高级联动','cross-parse':'交叉解析','anti-trace':'反追反穿','extreme-break':'极限突破','decode-challenge':'破译挑战','auth':'权限管理','api-doc':'API接口文档','prod-control':'后端控制','ai-train':'AI训练','fastapi-control':'FastAPI服务联动'
    };
    return { VERSION, MODULES };
  })();
  global.IndexConfig = IndexConfig;

  // ---------- Helpers ----------
  (function(g){
    const CFG = { ASSET_BASE:'./index-', API_BASE:'/api' };
    function withApiPrefix(url){
      if(!url||typeof url!=='string') return url;
      if(url.startsWith('/data/')) return url;
      if(url.startsWith('http://')||url.startsWith('https://')) return url;
      if(url.startsWith('/')) return CFG.API_BASE + (url.startsWith('/api')? url.replace(/^\/api/,'') : url);
      return url;
    }
    g.IDX = g.IDX || {};
    g.IDX.config = CFG;
    g.IDX.withApiPrefix = withApiPrefix;
  })(global);

  // ---------- Pub/Sub ----------
  global.IndexBus=(function(){
    const topics=new Map();
    function on(t,h){ if(!topics.has(t)) topics.set(t,new Set()); topics.get(t).add(h); return ()=>off(t,h);} 
    function off(t,h){ const s=topics.get(t); if(s){ s.delete(h);} }
    function emit(t,p){ const s=topics.get(t); if(s){ s.forEach(fn=>{ try{ fn(p);}catch(e){} }); } }
    return { on,off,emit };
  })();
  (function(g){
    const KEY='__idx_bus__';
    const bus={ publish(topic,payload){ try{ localStorage.setItem(KEY, JSON.stringify({topic,payload,ts:Date.now(),id:Math.random()})); }catch(e){} }, subscribe(handler){ g.__idxBusHandler = handler; } };
    window.addEventListener('storage', function(e){ if(e.key===KEY && e.newValue){ try{ const msg=JSON.parse(e.newValue); g.__idxBusHandler && g.__idxBusHandler(msg);}catch(_){}} });
    g.IDX=g.IDX||{}; g.IDX.bus=bus;
  })(global);

  // ---------- API Docs/Data ----------
  global.IndexAPI=(function(){
    function getKpis(){ return { totalTasks:42, doneTasks:17, progress:41 }; }
    function getModuleDoc(key){
      const docs={
        'param_deploy':{ title:'参数部署 · 规范说明', lines:[ '统一参数编辑、校验与下发；支持导入导出与版本化。','接口预留（建议）','获取参数配置（含版本、并发/深度/超时、UA、代理）','保存/下发参数配置（含导入导出、版本化）','参数校验（并发/深度/超时范围、代理连通性）','目标配置分级枚举：公开/个人/政府公开','风控识别（关键词与策略校验）','结果排序策略预览（权重/规则）','配置保存','配置加载','服务健康','事件联动' ] },
        'smart-schedule':{ title:'智能调度 · 规范说明', lines:[ '调度器启停、优先级与限流策略；支持重试与失败转移。','接口预留（建议）','启动调度器（限流、优先级）','停止调度器','调度器状态','AI识别服务注册（模型、路由）','AI联动编排（多模型流水线）','采集脚本通过API异步调用','失败回退与记录策略落盘' ] },
        'collect-task':{ title:'采集任务 · 规范说明', lines:[ '采集任务创建、批量导入、实时进度与失败重试。','接口预留（建议）','查询采集任务列表','创建采集任务（精准/模糊/关联）','表单校验（关键词/电话/邮箱/姓名/地区/地址/IP/域名/Telegram/WhatsApp/银行卡号/文件/图片）','采集任务详情','启动指定采集任务','停止指定采集任务' ] },
        'enum-task':{ title:'枚举任务 · 规范说明', lines:[ '字典/规则驱动的枚举扫描任务管理与结果采集。','接口预留（建议）','枚举任务列表','银行卡BIN校验','游戏卡枚举','虚拟卡枚举','虚拟币助词器（助记词）枚举','十六进制密钥枚举','32位密钥枚举','属性/规则/关键词配置','交叉联动执行','触发枚举扫描' ] },
        'recognize-task':{ title:'识别任务 · 规范说明', lines:[ '内容识别/OCR/分类等识别流程的提交与跟踪。','接口预留（建议）','提交识别任务（IP/域名/图片/文件/关键词）','识别状态','路由追踪与位置分析','DNS/ASN信息查询','组织名与关联实体查询','社交媒体链接聚合','跨模块智能协同解析与推理','bitby/OKX/telegram/whatsapp等软件线索聚合' ] },
        'crack-task':{ title:'破解任务 · 规范说明', lines:[ '口令/验证码等破解任务编排与执行监控。','接口预留','验证码自动破解处理','URL编码解码','解析渗透','网页解析','zip解锁','各app账号密码逻辑破解','安全防控破解','安卓手机密码破解','谷歌相册破解','银行卡号/日期/CVV校验/破解','B64解码','打码清除','启动破解任务','破解任务状态' ] },
        'status':{ title:'自动化状态 · 规范说明', lines:[ '实时监控各模块状态与进度。','接口预留','自动化运行总况','进度聚合','安全级别枚举：合规版/极限限制/突破限制/无视限制','应用安全级别+关键词理解策略','快速任务（自动降级）','自动识别验证码','自动收集','自动切换采集策略','自动化绕过与规避风险参数搭配进度聚合' ] },
        'log':{ title:'日志管理 · 规范说明', lines:[ '查看、导出、清理系统运行日志。','接口预留','任务部署日志','下载安装日志','IP登陆日志','功能使用日志','清理日志' ] },
        'workflow-deploy':{ title:'工作流部署 · 规范说明', lines:[ '编排式工作流部署、版本管理与一键发布回滚。','工作流列表','部署/回滚','基础逻辑1：入口→参数生成→策略决策→资源/输出','基础逻辑2：入口→预设参数→本地AI策略→语义/OCR/识别→策略决策→资源/输出','基础逻辑3：入口→参数→云AI策略→语义/OCR/识别→联动增强→复杂推理→本地AI→向量库→全功能联动→策略决策→参数生成→资源/输出','开启突破限制开关','高级逻辑：入口→参数→云AI策略→语义/OCR/识别→联动增强→复杂推理→返回本地AI→高级功能联动→生成策略→参数→资源/输出' ] }
      };
      return docs[key] || { title:'模块占位', lines:['暂无说明'] };
    }
    return { getKpis, getModuleDoc };
  })();

  // ---------- API wrapper ----------
  // 若存在模块化 api.js（ESM），则不重复定义；否则提供兜底 apiFetch
  (function(g){
    if (!g.IDX) g.IDX = {};
    if (!g.IDX.api){
      async function apiFetch(url, options){ const u=g.IDX.withApiPrefix(url); return fetch(u, options||{}); }
      g.IDX.api = { apiFetch };
    }
  })(global);

  // ---------- Permission ----------
  const Permission = (function(){
    const DEFAULT_ROLE='guest';
    const featureRoles={ 'auth':new Set(['admin']),'task':new Set(['admin','operator']),'monitor':new Set(['admin','operator','auditor']),'export':new Set(['admin','auditor']) };
    const getRoleFromEnv=()=>{ try{ const urlRole=new URLSearchParams(window.location.search).get('role'); if(urlRole) return urlRole; const lsRole=localStorage.getItem('user.role'); return lsRole||DEFAULT_ROLE; }catch(_){ return DEFAULT_ROLE; } };
    const currentRole=getRoleFromEnv();
    const canAccess=(featureKey)=>{ const roles=featureRoles[featureKey]; if(!roles) return true; return roles.has(currentRole); };
    const guardElement=(el,featureKey)=>{ try{ if(!canAccess(featureKey)){ el.classList.add('disabled'); el.setAttribute('aria-disabled','true'); el.title=`当前角色(${currentRole})无权限访问: ${featureKey}`; } }catch(_){ } };
    const applyGuards=()=>{ document.querySelectorAll('[data-feature]').forEach(el=>guardElement(el, el.getAttribute('data-feature'))); };
    return { currentRole, canAccess, applyGuards };
  })();
  global.Permission = Permission;

  // ---------- View Logic ----------
  function updateMiniKpis(){ const k=IndexAPI.getKpis(); const total=document.getElementById('task-stats-total2'); const done=document.getElementById('task-stats-done2'); const bar=document.getElementById('task-progress-bar2'); const txt=document.getElementById('task-progress-text2'); if(total) total.textContent=k.totalTasks; if(done) done.textContent=k.doneTasks; if(bar) bar.style.width=k.progress+'%'; if(txt) txt.textContent=k.progress+'%'; }
  function renderHome(){ const main=document.getElementById('main-content'); if(!main) return; const k=IndexAPI.getKpis(); main.innerHTML=`<div class="card"><div class="card-title">首页</div><div class="card-note">呈现正在运行的任务配置和任务进度，实时图形数据表、内容K线进度表、运行内容实时反馈与解决方案。</div><div class="kpi-strip" style="margin-top:10px;"><div class="kpi"><div class="label">任务总数</div><div class="value">${k.totalTasks}</div></div><div class="kpi"><div class="label">已完成</div><div class="value">${k.doneTasks}</div></div><div class="kpi"><div class="label">进度</div><div class="value">${k.progress}%</div></div></div><div class="module-grid" style="margin-top:10px;">
  <div class="module-card"><h4>弹窗嵌套演示</h4><div class="placeholder"><div class="btn-row"><button class="btn" id="btn-open-modal">打开一级弹窗</button><button class="btn" id="btn-open-nested">打开嵌套弹窗</button></div><div class="muted" style="margin-top:6px;">验证事件阻止、Modal 栈与 LIFO 关闭。</div></div></div>
  <div class="module-card"><h4>分页演示</h4><div class="placeholder"><div id="demo-page-container"></div><div class="muted" style="margin-top:6px;">利用 Pagination 组件进行列表换页回调。</div></div></div>
  <div class="module-card"><h4>Fuzz 报告入口</h4><div class="placeholder"><div class="btn-row"><a class="btn" href="../reports/fuzz_report.md" target="_blank">查看最新 Fuzz 报告</a></div><div class="muted" style="margin-top:6px;">可通过 CLI 生成到此路径。</div></div></div>
  <div class="module-card"><h4>采集报告入口</h4><div class="placeholder"><div class="btn-row"><a class="btn" href="../reports/collectors_report.md" target="_blank">查看最新采集报告</a></div><div class="muted" style="margin-top:6px;">合并多源采集结果。</div></div></div>
  <div class="module-card"><h4>风控检测演示（占位）</h4><div class="placeholder"><div class="btn-row"><button class="btn" id="btn-risk-progress">请求 /api/auto/risk/progress</button><button class="btn" id="btn-captcha-demo">请求 /api/crack/captcha（模拟上传）</button></div><pre class="muted" id="risk-out" style="margin-top:8px;white-space:pre-wrap;">输出将在此显示</pre></div></div>
  <div class="module-card"><h4>实时图形数据表（占位）</h4><div class="placeholder"><table class="table"><thead><tr><th>指标</th><th>当前值</th><th>变化</th></tr></thead><tbody><tr><td>吞吐</td><td>123</td><td>+3%</td></tr><tr><td>延迟</td><td>85ms</td><td>-1%</td></tr><tr><td>错误率</td><td>0.4%</td><td>-0.1%</td></tr></tbody></table></div></div>
  <div class="module-card"><h4>内容K线进度表（占位）</h4><div class="placeholder"><div class="progress-bar"><div class="progress-fill" style="width:${k.progress}%"></div></div><div class="muted" style="margin-top:6px;">进度 ${k.progress}%</div></div></div>
  <div class="module-card"><h4>运行内容实时反馈与解决方案（占位）</h4><div class="placeholder"><ul class="list"><li>反馈：节点 A 负载偏高，建议限流至 80%</li><li>反馈：代理池连接抖动，建议切换备用池</li><li>方案：OCR 阶段失败率提升，建议替换模型 v2</li></ul></div></div>
  </div></div>`; }
  let currentView = null;
  function renderModule(key){ const main=document.getElementById('main-content'); if(!main) return; if(currentView && typeof currentView.unmount==='function'){ try{ currentView.unmount(); }catch(_){} } const info=IndexAPI.getModuleDoc(key); const title=IndexConfig.MODULES[key]||info.title; const k=IndexAPI.getKpis(); const body=`<div class="placeholder"><div class="muted">${info.title}</div><ul class="list">${info.lines.map(l=>`<li>${l}</li>`).join('')}</ul></div><div style="margin-top:12px;" class="btn-row"><button class="btn" data-action="save">配置保存</button><button class="btn" data-action="load">配置加载</button><button class="btn" data-action="health">服务健康</button></div>`; main.innerHTML=`<div class="card"><div class="kpi-strip"><div class="kpi"><div class="label">任务总数</div><div class="value" id="kpi-total">${k.totalTasks}</div></div><div class="kpi"><div class="label">已完成</div><div class="value" id="kpi-done">${k.doneTasks}</div></div><div class="kpi"><div class="label">进度</div><div class="value" id="kpi-progress">${k.progress}%</div></div></div><div class="card-title">${title}</div>${body}</div>`; currentView={ unmount(){ document.querySelectorAll('.btn[data-action]').forEach(btn=>{ btn.replaceWith(btn.cloneNode(true)); }); } }; }
  function renderTasks(){ const main=document.getElementById('main-content'); if(!main) return; const k=IndexAPI.getKpis(); main.innerHTML=`<div class="card"><div class="card-title">任务</div><div class="card-note">任务总数、任务逻辑、已完成任务数、所有内容参数配置后的说明呈现；执行按钮：确定 / 启动 / 停止（占位）。</div><div class="kpi-strip" style="margin-top:10px;"><div class="kpi"><div class="label">任务总数</div><div class="value">${k.totalTasks}</div></div><div class="kpi"><div class="label">已完成</div><div class="value">${k.doneTasks}</div></div><div class="kpi"><div class="label">进度</div><div class="value">${k.progress}%</div></div></div><div class="placeholder" style="margin-top:10px;"><h4 style="margin:0 0 6px; color:#667eea;">任务逻辑（占位）</h4><ul class="list"><li>入口 → 参数生成 → 策略决策 → 资源/输出</li><li>入口 → 预设参数 → 本地AI策略 → 语义/OCR/识别 → 策略决策 → 资源/输出</li></ul></div><div class="btn-row" style="margin-top:12px;"><button class="btn">确定</button><button class="btn">启动</button><button class="btn">停止</button></div></div>`; }
  function renderStats(){ const main=document.getElementById('main-content'); if(!main) return; const k=IndexAPI.getKpis(); main.innerHTML=`<div class="card"><div class="card-title">统计</div><div class="card-note">实时任务统计（占位）。</div><div class="module-grid" style="margin-top:10px;"><div class="module-card"><h4>任务统计（占位）</h4><div class="placeholder"><table class="table"><thead><tr><th>类型</th><th>数量</th><th>完成</th></tr></thead><tbody><tr><td>采集</td><td>${Math.ceil(k.totalTasks*0.4)}</td><td>${Math.ceil(k.doneTasks*0.5)}</td></tr><tr><td>枚举</td><td>${Math.ceil(k.totalTasks*0.3)}</td><td>${Math.ceil(k.doneTasks*0.3)}</td></tr><tr><td>识别</td><td>${Math.ceil(k.totalTasks*0.3)}</td><td>${Math.ceil(k.doneTasks*0.2)}</td></tr></tbody></table></div></div><div class="module-card"><h4>占位图（简易进度）</h4><div class="placeholder"><div class="progress-bar"><div class="progress-fill" style="width:${k.progress}%"></div></div><div class="muted" style="margin-top:6px;">总体进度 ${k.progress}%</div></div></div></div></div>`; }

  function bindMenu(){ document.querySelectorAll('.menu-item[data-module]').forEach(el=>{ el.addEventListener('click', function(e){ e.preventDefault(); document.querySelectorAll('.menu-item').forEach(i=>i.classList.remove('active')); this.classList.add('active'); renderModule(this.getAttribute('data-module')); }); }); }
  function bindTopNav(){ const navHome=document.getElementById('nav-home'); const navTask=document.getElementById('nav-task'); const navStats=document.getElementById('nav-stats'); if(navHome){ navHome.addEventListener('click', function(e){ e.preventDefault(); if(currentView && typeof currentView.unmount==='function'){ try{ currentView.unmount(); }catch(_){} } setActiveTop(this); renderHome(); }); } if(navTask){ navTask.addEventListener('click', function(e){ e.preventDefault(); if(currentView && typeof currentView.unmount==='function'){ try{ currentView.unmount(); }catch(_){} } setActiveTop(this); renderTasks(); }); } if(navStats){ navStats.addEventListener('click', function(e){ e.preventDefault(); if(currentView && typeof currentView.unmount==='function'){ try{ currentView.unmount(); }catch(_){} } setActiveTop(this); renderStats(); }); } }
  function setActiveTop(el){ document.querySelectorAll('.header .nav a').forEach(a=>a.classList.remove('active')); el.classList.add('active'); }

  function initFrameInteractions(){
    const sideToggle = document.getElementById('sideToggle');
    const sideBar = document.getElementById('sideBar');
    if(sideToggle && sideBar){ sideToggle.addEventListener('click', function(){ sideBar.classList.toggle('collapsed'); this.classList.toggle('collapsed'); }); }
    document.querySelectorAll('.menu-item:not([data-module])').forEach(item => {
      item.addEventListener('click', function(e){ e.preventDefault(); document.querySelectorAll('.menu-item').forEach(i=>i.classList.remove('active')); this.classList.add('active'); });
    });
    const sharedConfig = { apiBase: '/api', user: 'Admin', ts: Date.now() };
    localStorage.setItem('yl_shared_config', JSON.stringify(sharedConfig));
    document.querySelectorAll('a.nav-link[data-target]').forEach(a=>{
      a.addEventListener('click', function(e){ e.preventDefault(); sessionStorage.setItem('fromIndex', '1'); const url = this.getAttribute('data-target'); alert('独立静态占位页：已模拟跳转到 ' + url); });
    });
  }

  function init(){
    console.log('Index 子站就绪');
    if (global.Permission && typeof global.Permission.applyGuards === 'function') {
      global.Permission.applyGuards();
    }
    renderHome();
    updateMiniKpis();
    bindMenu();
    bindTopNav();
    initFrameInteractions();
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }
})(window);
