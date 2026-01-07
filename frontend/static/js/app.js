import { createApp } from 'vue';
import { createRouter, createWebHashHistory } from 'vue-router';
import { createPinia } from 'pinia';
import { createI18n } from 'vue-i18n';
import App from './App.vue';
import { useAppStore } from './stores/store.js';
import { registerSW } from 'workbox-window';

// 懒加载组件
const Home = () => import('./components/Home.vue');
const Run = () => import('./components/Run.vue');
const Monitor = () => import('./components/Monitor.vue');
const ApiDoc = () => import('./components/ApiDoc.vue');
const VisualPipeline = () => import('./components/VisualPipeline.vue');
const Rbac = () => import('./components/Rbac.vue');
const AiDemo = () => import('./components/AiDemo.vue');
const PhonePanel = () => import('./components/PhonePanel.vue');
const DemoPanel = () => import('./components/DemoPanel.vue');

const routes = [
  { path: '/', component: Home },
  { path: '/run', component: Run },
  { path: '/monitor', component: Monitor },
  { path: '/api-doc', component: ApiDoc },
  { path: '/visual-pipeline', component: VisualPipeline },
  { path: '/rbac', component: Rbac },
  { path: '/ai-demo', component: AiDemo },
  { path: '/phone', component: PhonePanel },
  { path: '/demo', component: DemoPanel },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

// 国际化配置
const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh',
  fallbackLocale: 'en',
  messages: {
    zh: {
      nav: {
        home: '首页',
        run: '任务执行',
        monitor: '系统监控',
        apiDoc: 'API文档',
        visualPipeline: '可视化流水线',
        rbac: '权限管理',
        aiDemo: 'AI演示'
      },
      common: {
        loading: '加载中...',
        error: '错误',
        success: '成功',
        confirm: '确认',
        cancel: '取消',
        save: '保存',
        delete: '删除',
        theme: '切换主题'
      },
      status: {
        online: '在线',
        offline: '离线',
        running: '运行中',
        stopped: '已停止'
      }
    },
    en: {
      nav: {
        home: 'Home',
        run: 'Task Execution',
        monitor: 'System Monitor',
        apiDoc: 'API Documentation',
        visualPipeline: 'Visual Pipeline',
        rbac: 'RBAC Management',
        aiDemo: 'AI Demo'
      },
      common: {
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        confirm: 'Confirm',
        cancel: 'Cancel',
        save: 'Save',
        delete: 'Delete',
        theme: 'Toggle Theme'
      },
      status: {
        online: 'Online',
        offline: 'Offline',
        running: 'Running',
        stopped: 'Stopped'
      }
    }
  }
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const store = useAppStore();
  if (!store.user && to.path !== '/') {
    // 检查权限
    next('/');
  } else {
    next();
  }
});

const pinia = createPinia();

const app = createApp(App);
app.use(router);
app.use(pinia);
app.use(i18n);
app.mount('#app');

// PWA Service Worker 注册
if ('serviceWorker' in navigator) {
  registerSW({
    onNeedRefresh() {
      // 当新版本可用时显示更新提示
      if (confirm('新版本可用，是否刷新？')) {
        window.location.reload();
      }
    },
    onOfflineReady() {
      console.log('应用已准备好离线使用');
    }
  });
}