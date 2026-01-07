<template>
  <div id="app">
    <header id="topbar">
      <div class="header-controls">
        <button id="theme-toggle" class="btn" @click="toggleTheme">{{ $t('common.theme') }}</button>
        <select v-model="currentLocale" @change="changeLanguage" class="language-selector">
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </div>
    </header>
    <nav class="main-nav">
      <ul>
        <li><router-link to="/">{{ $t('nav.home') }}</router-link></li>
        <li><router-link to="/run">{{ $t('nav.run') }}</router-link></li>
        <li><router-link to="/monitor">{{ $t('nav.monitor') }}</router-link></li>
        <li><router-link to="/api-doc">{{ $t('nav.apiDoc') }}</router-link></li>
        <li><router-link to="/visual-pipeline">{{ $t('nav.visualPipeline') }}</router-link></li>
        <li><router-link to="/rbac">{{ $t('nav.rbac') }}</router-link></li>
        <li><router-link to="/ai-demo">{{ $t('nav.aiDemo') }}</router-link></li>
      </ul>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n';

export default {
  setup() {
    const { t, locale } = useI18n();
    return { t, locale };
  },
  data() {
    return {
      currentLocale: localStorage.getItem('locale') || 'zh'
    };
  },
  mounted() {
    // PWA Service Worker 已在 app.js 中注册
  },
  methods: {
    toggleTheme() {
      document.body.classList.toggle('dark-theme');
      localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    },
    changeLanguage() {
      this.locale.value = this.currentLocale;
      localStorage.setItem('locale', this.currentLocale);
    }
  },
  watch: {
    currentLocale(newVal) {
      this.locale.value = newVal;
    }
  }
}
</script>

<style>
/* 头部样式 */
.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.language-selector {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

/* 导航样式 */
.main-nav ul {
  list-style: none;
  display: flex;
  gap: 20px;
  padding: 10px;
  flex-wrap: wrap;
}
.main-nav a {
  text-decoration: none;
  color: #667eea;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background 0.3s;
}
.main-nav a:hover, .main-nav a.router-link-active {
  background: #e0eafc;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-nav ul {
    flex-direction: column;
    gap: 10px;
  }
  .header-controls {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>