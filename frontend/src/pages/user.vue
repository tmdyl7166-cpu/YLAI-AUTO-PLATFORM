<template>
  <div>
    <h2>用户中心</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div class="profile">
        <h3>个人信息</h3>
        <p>用户名: {{ profile.username }}</p>
        <p>角色: {{ profile.role }}</p>
        <p>邮箱: {{ profile.email }}</p>
      </div>
      <div class="history">
        <h3>历史任务</h3>
        <ul>
          <li v-for="task in history" :key="task.id">
            {{ task.name }} - {{ task.status }}
          </li>
        </ul>
      </div>
      <div class="rbac">
        <h3>权限管理</h3>
        <ul>
          <li v-for="perm in profile.permissions" :key="perm">{{ perm }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'UserPage',
  data() {
    return {
      loading: true,
      error: null,
      profile: {},
      history: []
    }
  },
  async mounted() {
    await this.loadUser();
  },
  methods: {
    async loadUser() {
      try {
        // 可联动注册表 user/profile、rbac
        const resp = await fetch('/api/user/profile');
        this.profile = await resp.json();
        const hist = await fetch('/api/user/history');
        this.history = await hist.json();
      } catch (err) {
        this.error = '加载用户信息失败: ' + err.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
<style scoped>
.profile, .history, .rbac { margin-bottom: 20px; }
</style>