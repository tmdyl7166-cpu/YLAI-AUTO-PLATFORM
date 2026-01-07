<template>
  <div id="app" class="app-wrapper">
    <nav v-if="showNav" class="app-nav">
      <div class="nav-brand">YLAI-AUTO-PLATFORM</div>
      <ul class="nav-links">
        <li><router-link to="/" :class="{ active: isActive('/') }">首页</router-link></li>
        <li><router-link to="/run" :class="{ active: isActive('/run') }">运行任务</router-link></li>
        <li><router-link to="/monitor" :class="{ active: isActive('/monitor') }">监控面板</router-link></li>
        <li><router-link to="/api-doc" :class="{ active: isActive('/api-doc') }">API文档</router-link></li>
        <li><router-link to="/visual-pipeline" :class="{ active: isActive('/visual-pipeline') }">可视化编排</router-link></li>
        <li><router-link to="/rbac" :class="{ active: isActive('/rbac') }">权限管理</router-link></li>
        <li><router-link to="/settings" :class="{ active: isActive('/settings') }">设置</router-link></li>
        <li><router-link to="/about" :class="{ active: isActive('/about') }">关于</router-link></li>
      </ul>
    </nav>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" :key="$route.path" />
        </Transition>
      </router-view>
    </main>

    <footer v-if="showNav" class="app-footer">
      <p>&copy; 2025 YLAI-AUTO-PLATFORM. All rights reserved.</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      showNav: true
    }
  },
  computed: {
    currentPath() {
      return this.$route?.path || '/'
    }
  },
  methods: {
    isActive(path) {
      return this.$route?.path === path
    }
  },
  watch: {
    $route(to) {
      // 隐藏登录页面的导航
      this.showNav = to.name !== 'Login'
    }
  },
  mounted() {
    this.$watch(
      () => this.$route.name,
      () => {
        this.showNav = this.$route.name !== 'Login'
      }
    )
  }
}
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-nav {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  letter-spacing: 0.5px;
}

.nav-links {
  list-style: none;
  display: flex;
  gap: 2rem;
  margin: 0;
  padding: 0;
}

.nav-links a {
  color: white;
  text-decoration: none;
  transition: opacity 0.2s;
  font-weight: 500;
}

.nav-links a:hover {
  opacity: 0.8;
}

.nav-links a.active {
  border-bottom: 2px solid white;
  padding-bottom: 0.25rem;
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: #f5f5f5;
  color: #666;
  padding: 2rem;
  text-align: center;
  border-top: 1px solid #ddd;
  margin-top: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .app-nav {
    flex-direction: column;
    gap: 1rem;
  }

  .nav-links {
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: center;
  }
}
</style>
