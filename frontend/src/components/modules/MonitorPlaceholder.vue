<template>
  <div class="monitor-placeholder">
    <h3>监控中心</h3>
    <div class="placeholder-content">
      <p>系统状态监控与告警</p>
      <div class="features">
        <div class="feature-item">
          <h4>性能监控</h4>
          <p>CPU、内存、磁盘使用率</p>
        </div>
        <div class="feature-item">
          <h4>健康检查</h4>
          <p>服务可用性监控</p>
        </div>
        <div class="feature-item">
          <h4>告警通知</h4>
          <p>异常情况通知</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MonitorPlaceholder'
}
</script>

<style scoped>
.monitor-placeholder {
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 20px;
  margin: 10px 0;
}

.placeholder-content h3 {
  margin-top: 0;
  color: #6c757d;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.feature-item {
  background: white;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.feature-item h4 {
  margin: 0 0 8px 0;
  color: #495057;
}

.feature-item p {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
}
</style>