// stripped page controller
void 0;
import { showToast } from '/static/js/components/toast.js';
window.Toast = { show: (msg, level='info') => showToast(msg, level) };

(function(){
  const i18n = {
    zh: { account:'账号 / 邮箱', password:'密码', login:'登录 YL 多功能检测仪', remember:'记住我', forgot:'忘记密码？', success:'登录成功，正在跳转…', error:'账号或密码错误', neterr:'网络或服务器错误，请稍后重试', env:'环境：生产', tz:'当前时区', english:'English', chinese:'中文', placeholderAcc:'请输入账号或邮箱', placeholderPwd:'请输入密码', minAcc:'账号长度至少 3 字符', minPwd:'密码至少 6 位', oauth:'社交登录占位', agree:'登录即表示您同意', terms:'服务条款', privacy:'隐私政策', panelTitle:'欢迎使用 YL 多功能检测仪', panelDesc:'一站式检测平台，融合了实时监控、爬虫策略联动、规则管理和 AI 协助分析。登录后可访问项目控制台与监控面板。', features:['实时任务监控','智能规则管理','API 调试工具','数据可视化'], note:'此页面会调用后端登录并存储 token。' },
    en: { account:'Account / Email', password:'Password', login:'Login YL Detector', remember:'Remember me', forgot:'Forgot password?', success:'Login success, redirecting…', error:'Invalid account or password', neterr:'Network/server error, try again later', env:'Env: Production', tz:'Timezone', english:'中文', chinese:'English', placeholderAcc:'Enter account or email', placeholderPwd:'Enter password', minAcc:'Account must be at least 3 chars', minPwd:'Password must be at least 6 chars', oauth:'Social login placeholder', agree:'By logging in you agree to', terms:'Terms of Service', privacy:'Privacy Policy', panelTitle:'Welcome to YL Detector', panelDesc:'One-stop detection platform with real-time monitoring, crawler strategy, rule management and AI analysis. Login to access console and monitor.', features:['Realtime Task Monitor','Smart Rule Management','API Debug Tool','Data Visualization'], note:'This page will call backend login and store token.' }
  };
  let lang = 'zh';
  function setLang(newLang){
    lang = newLang;
    document.getElementById('langSwitchBtn').textContent = i18n[lang][lang==='zh'?'english':'chinese'];
    document.getElementById('envInfo').textContent = i18n[lang].env;
    document.getElementById('tzInfo').textContent = i18n[lang].tz+': '+Intl.DateTimeFormat().resolvedOptions().timeZone;
    document.querySelector('label[for="account"]').textContent = i18n[lang].account;
    document.querySelector('label[for="password"]').textContent = i18n[lang].password;
    document.getElementById('loginBtn').textContent = i18n[lang].login;
    document.querySelector('.checkbox').innerHTML = `<input id="remember" type="checkbox" /> ${i18n[lang].remember}`;
    document.querySelector('.link.small').textContent = i18n[lang].forgot;
    document.getElementById('account').placeholder = i18n[lang].placeholderAcc;
    document.getElementById('password').placeholder = i18n[lang].placeholderPwd;
    document.getElementById('panel-title').textContent = i18n[lang].panelTitle;
    document.querySelector('.panel p').textContent = i18n[lang].panelDesc;
    document.querySelectorAll('.feature').forEach((el,i)=>{ el.lastChild.textContent = i18n[lang].features[i]; });
    document.querySelector('.small').textContent = i18n[lang].note;
  }
  document.getElementById('langSwitchBtn').onclick = function(){ setLang(lang==='zh'?'en':'zh'); };
  setLang(lang);

  const form = document.getElementById('loginForm');
  const account = document.getElementById('account');
  const password = document.getElementById('password');
  const loginBtn = document.getElementById('loginBtn');
  const togglePass = document.getElementById('togglePass');
  const formMessage = document.getElementById('formMessage');
  const accountError = document.getElementById('accountError');
  const passwordError = document.getElementById('passwordError');

  togglePass.addEventListener('click', () => {
    const isPwd = password.type === 'password';
    password.type = isPwd ? 'text' : 'password';
    togglePass.textContent = isPwd ? (lang==='zh'?'隐藏':'Hide') : (lang==='zh'?'显示':'Show');
  });

  function validate(){
    let ok = true;
    accountError.style.display = 'none';
    passwordError.style.display = 'none';
    formMessage.textContent = '';
    const accVal = account.value.trim();
    if(!accVal){ accountError.style.display='block'; accountError.textContent=i18n[lang].placeholderAcc; ok=false; }
    else if(accVal.length<3){ accountError.style.display='block'; accountError.textContent=i18n[lang].minAcc; ok=false; }
    const pwdVal = password.value;
    if(!pwdVal){ passwordError.style.display='block'; passwordError.textContent=i18n[lang].placeholderPwd; ok=false; }
    else if(pwdVal.length<6){ passwordError.style.display='block'; passwordError.textContent=i18n[lang].minPwd; ok=false; }
    return ok;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if(!validate()) return;
    loginBtn.disabled = true;
    loginBtn.textContent = lang==='zh'?'登录中...':'Logging in...';
    try {
      const res = await loginRequest({ account: account.value.trim(), password: password.value });
      if(res && res.success){
        const role = res.role || 'user';
        try { localStorage.setItem('yl_user_role', role); } catch(_){}
        formMessage.innerHTML = `<div class="success">${i18n[lang].success}（角色：${role}）</div>`;
        const target = '/pages/run.html';
        setTimeout(() => { window.location.href = target; }, 600);
      } else {
        const msg = (res && res.message) ? res.message : i18n[lang].error;
        formMessage.innerHTML = `<div class="error">${msg}</div>`;
      }
    } catch (err){
      console.error(err);
      formMessage.innerHTML = `<div class="error">${i18n[lang].neterr}</div>`;
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = i18n[lang].login;
    }
  });

  function social(provider){
    window.Toast.show((lang==='zh'?i18n.zh.oauth:i18n.en.oauth)+': '+provider+(lang==='zh'?'（请在后端实现 OAuth）':' (implement OAuth in backend)'), 'info');
  }
  window.social = social;

  async function loginRequest(payload){
    const url = '/api/auth/login';
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: payload.account, password: payload.password })
    });
    if(!resp.ok){
      const text = await resp.text().catch(()=> '');
      return { success:false, message: text || (lang==='zh'? '登录失败' : 'Login failed') };
    }
    const data = await resp.json();
    if(data && data.token){
      try { window.authSetToken ? window.authSetToken(data.token) : (window.setToken && window.setToken(data.token)); } catch(e){ console.warn('set token failed', e); }
    }
    let role = data.role || 'user';
    try {
      const u = (payload && payload.account) ? String(payload.account).toLowerCase() : '';
      if(!data.role){
        if(u==='yeling'){ role = 'superadmin'; }
        else if(u==='admin'){ role = 'admin'; }
        else { role = 'user'; }
      }
    } catch(_){}
    try{ sessionStorage.setItem('from_login', '1'); }catch(_){}
    return { success:true, role, user: data.user, token: data.token };
  }

  (function autoRedirect(){
    try {
      const t = window.authGetToken ? window.authGetToken() : (window.getToken && window.getToken());
      if(t){ window.location.href = '/pages/monitor.html'; }
    } catch(_){}
  })();
})();
