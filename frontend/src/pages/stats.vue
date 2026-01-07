<template>
  <div>
    <h2>统计分析</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card" v-for="stat in stats" :key="stat.key">
          <h3>{{ stat.label }}</h3>
          <p>调用次数: {{ stat.calls }}</p>
          <p>成功率: {{ stat.successRate }}%</p>
          <p>异常数: {{ stat.errors }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'StatsPage',
  data() {
    return {
      loading: true,
      error: null,
      stats: []
    }
  },
  async mounted() {
    await this.loadStats();
  },
  methods: {
    async loadStats() {
      try {
        const resp = await fetch('/api/metrics/stats');
        this.stats = await resp.json();
      } catch (err) {
        this.error = '加载统计失败: ' + err.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
.stat-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
</style>