import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/index.vue')
  },
  {
    path: '/run',
    name: 'Run',
    component: () => import('@/pages/run.vue')
  },
  {
    path: '/api-doc',
    name: 'ApiDoc',
    component: () => import('@/pages/api-doc.vue')
  },
  {
    path: '/api-map',
    name: 'ApiMap',
    component: () => import('@/pages/api-map.vue')
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('@/pages/monitor.vue')
  },
  {
    path: '/visual-pipeline',
    name: 'VisualPipeline',
    component: () => import('@/pages/visual_pipeline.vue')
  },
  {
    path: '/rbac',
    name: 'Rbac',
    component: () => import('@/pages/rbac.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/login.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/settings.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/pages/about.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/pages/history.vue')
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/pages/stats.vue')
  },
  {
    path: '/user',
    name: 'User',
    component: () => import('@/pages/user.vue')
  },
  // 404 处理
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  strict: false,
  sensitive: false
});

// 路由守卫：记录导航和错误
router.beforeEach((to, from, next) => {
  console.log(`导航从 ${from.path} 到 ${to.path}`);
  next();
});

router.afterEach((to, from, failure) => {
  if (failure) {
    console.error(`导航失败: ${to.path}`, failure);
  }
});

export default router;
