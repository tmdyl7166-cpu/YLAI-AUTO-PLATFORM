<template>
  <div>
    <h2>系统设置</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <form @submit.prevent="saveSettings">
        <div v-for="item in settings" :key="item.key" class="setting-item">
          <label>{{ item.label }}:</label>
          <input v-model="item.value" :type="item.type || 'text'" />
        </div>
        <button type="submit">保存设置</button>
      </form>
    </div>
  </div>
</template>
<script>
export default {
  name: 'SettingsPage',
  data() {
    return {
      loading: true,
      error: null,
      settings: []
    }
  },
  async mounted() {
    await this.loadSettings();
  },
  methods: {
    async loadSettings() {
      try {
        const resp = await fetch('/api/settings/config');
        this.settings = await resp.json();
      } catch (err) {
        this.error = '加载设置失败: ' + err.message;
      } finally {
        this.loading = false;
      }
    },
    async saveSettings() {
      await fetch('/api/settings/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.settings)
      });
      alert('设置已保存');
    }
  }
}
</script>
<style scoped>
.setting-item { margin-bottom: 15px; }
</style>