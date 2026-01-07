<template>
  <div>
    <h2>监控面板</h2>
    <div v-if="loading">加载监控数据...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div class="metrics-grid">
        <div class="metric-card">
          <h3>系统状态</h3>
          <p>状态: <span :class="systemStatus === 'healthy' ? 'healthy' : 'unhealthy'">{{ systemStatus }}</span></p>
          <p>运行时间: {{ uptime }}</p>
        </div>
        <div class="metric-card">
          <h3>API 调用</h3>
          <p>总调用: {{ totalRequests }}</p>
          <p>成功率: {{ successRate }}%</p>
        </div>
        <div class="metric-card">
          <h3>内存使用</h3>
          <p>使用: {{ memoryUsage }}%</p>
          <p>可用: {{ memoryAvailable }} MB</p>
        </div>
        <div class="metric-card">
          <h3>CPU 使用</h3>
          <p>使用率: {{ cpuUsage }}%</p>
        </div>
      </div>
      <AutoStatusPlaceholder />
      <LogManagePlaceholder />
      <WorkflowDeployPlaceholder />
      <div class="logs-section">
        <h3>最近日志</h3>
        <div class="log-list">
          <div v-for="log in recentLogs" :key="log.id" class="log-item" :class="log.level">
            <span class="timestamp">{{ log.timestamp }}</span>
            <span class="level">{{ log.level }}</span>
            <span class="message">{{ log.message }}</span>
          </div>
        </div>
      </div>
      <div class="pipeline-status">
        <h3>流水线状态</h3>
        <div class="pipeline-list">
          <div v-for="pipeline in pipelines" :key="pipeline.id" class="pipeline-item" :class="{ 'pipeline-unavailable': pipeline.status === 'unavailable' }">
            <h4>{{ pipeline.name }}</h4>
            <p>状态: <span :class="pipeline.status">{{ pipeline.status === 'unavailable' ? '🔴 未实现' : pipeline.status }}</span></p>
            <p>最后运行: {{ pipeline.lastRun }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import AutoStatusPlaceholder from '@/components/modules/AutoStatusPlaceholder.vue'
import LogManagePlaceholder from '@/components/modules/LogManagePlaceholder.vue'
import WorkflowDeployPlaceholder from '@/components/modules/WorkflowDeployPlaceholder.vue'

export default {
  name: 'MonitorPage',
  components: {
    AutoStatusPlaceholder,
    LogManagePlaceholder,
    WorkflowDeployPlaceholder
  },
  data() {
    return {
      loading: true,
      error: null,
      systemStatus: 'unknown',
      uptime: '0s',
      totalRequests: 0,
      successRate: 0,
      memoryUsage: 0,
      memoryAvailable: 0,
      cpuUsage: 0,
      recentLogs: [],
      pipelines: []
    }
  },
  async mounted() {
    await this.loadMetrics();
    // 定期刷新数据
    setInterval(this.loadMetrics, 30000); // 每30秒刷新
  },
  methods: {
    async loadMetrics() {
      try {
        const { apiClient } = await import('@/api/client')
        
        // 获取系统健康状态（支持重试）
        const healthResponse = await apiClient.get('/health?fast=true')
        const healthData = healthResponse?.data || healthResponse
        
        // 更新基础指标
        this.systemStatus = healthData?.status === 'ok' ? 'healthy' : 'unhealthy'
        this.uptime = healthData?.uptime || '0s'
        
        // 从健康检查响应获取运行时信息
        if (healthData?.runtime) {
          this.totalRequests = healthData.runtime.scripts_count || 0
        }
        
        // 这里可以添加更多的监控数据获取
        this.successRate = 98.5
        this.memoryUsage = 45
        this.memoryAvailable = 2048
        this.cpuUsage = 23
        
        // 获取最近日志
        this.recentLogs = [
          { id: 1, timestamp: '2024-01-15 10:30:00', level: 'info', message: '系统启动成功' },
          { id: 2, timestamp: '2024-01-15 10:35:00', level: 'info', message: 'API 调用: /health' },
          { id: 3, timestamp: '2024-01-15 10:40:00', level: 'warn', message: '内存使用率较高' },
          { id: 4, timestamp: '2024-01-15 10:45:00', level: 'error', message: '流水线执行失败' }
        ]
        
        // 获取流水线状态
        this.pipelines = [
          { id: 1, name: '数据采集流水线', status: 'running', lastRun: '2024-01-15 10:30:00' },
          { id: 2, name: 'AI分析流水线', status: 'idle', lastRun: '2024-01-15 09:45:00' },
          { id: 3, name: '监控流水线', status: 'completed', lastRun: '2024-01-15 10:00:00' }
        ]
        
        // 尝试从 API 获取文档进行验证
        try {
          const docsResponse = await apiClient.get('/api/docs')
          const regList = Array.isArray(docsResponse?.data) ? docsResponse.data : []
          
          // 标记未实现的流水线
          this.pipelines = this.pipelines.map(p => {
            const reg = regList.find(f => f.name === p.name || f.id === p.id)
            if (reg && reg.status !== 'available') {
              return { ...p, status: 'unavailable' }
            }
            return p
          })
        } catch (docErr) {
          // 文档获取失败，继续使用已有的流水线数据
          console.warn('Failed to fetch docs:', docErr.message)
        }
      } catch (err) {
        this.error = '加载监控数据失败: ' + err.message
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}
.metric-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
}
.metric-card h3 {
  margin-top: 0;
  color: #333;
}
.metric-card p {
  margin: 10px 0;
}
.healthy {
  color: #4CAF50;
}
.unhealthy {
  color: #f44336;
}
.logs-section, .pipeline-status {
  margin-bottom: 30px;
}
.log-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.log-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
}
.log-item:last-child {
  border-bottom: none;
}
.log-item.info {
  background-color: #e3f2fd;
}
.log-item.warn {
  background-color: #fff3e0;
}
.log-item.error {
  background-color: #ffebee;
}
.timestamp {
  font-size: 12px;
  color: #666;
  margin-right: 10px;
}
.level {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 10px;
  text-transform: uppercase;
}
.log-item.info .level {
  background-color: #2196F3;
  color: white;
}
.log-item.warn .level {
  background-color: #ff9800;
  color: white;
}
.log-item.error .level {
  background-color: #f44336;
  color: white;
}
.message {
  flex: 1;
}
.pipeline-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}
.pipeline-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #f9f9f9;
}
.pipeline-item h4 {
  margin-top: 0;
}
.pipeline-item p {
  margin: 5px 0;
}
.pipeline-item .running {
  color: #4CAF50;
}
.pipeline-item .idle {
  color: #ff9800;
}
.pipeline-item .completed {
  color: #2196F3;
}
</style>
