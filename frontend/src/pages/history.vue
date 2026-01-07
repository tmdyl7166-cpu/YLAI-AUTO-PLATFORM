<template>
  <div>
    <h2>任务历史</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <table class="history-table">
        <thead>
          <tr>
            <th>任务名</th>
            <th>状态</th>
            <th>结果</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.name }}</td>
            <td>{{ task.status }}</td>
            <td>{{ task.result }}</td>
            <td><button @click="retryTask(task.id)">重试</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script>
export default {
  name: 'HistoryPage',
  data() {
    return {
      loading: true,
      error: null,
      tasks: []
    }
  },
  async mounted() {
    await this.loadHistory();
  },
  methods: {
    async loadHistory() {
      try {
        const resp = await fetch('/api/task/history');
        this.tasks = await resp.json();
      } catch (err) {
        this.error = '加载任务历史失败: ' + err.message;
      } finally {
        this.loading = false;
      }
    },
    async retryTask(id) {
      // 可联动注册表，重试任务
      await fetch(`/api/task/retry/${id}`, { method: 'POST' });
      await this.loadHistory();
    }
  }
}
</script>
<style scoped>
.history-table { width: 100%; border-collapse: collapse; }
.history-table th, .history-table td { border: 1px solid #ddd; padding: 8px; }
</style>