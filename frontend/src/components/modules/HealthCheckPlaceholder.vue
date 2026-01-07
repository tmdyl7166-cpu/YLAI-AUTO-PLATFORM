<template>
  <div class="health-check-placeholder">
    <h3>健康检测</h3>
    <div class="placeholder-content">
      <p>系统健康监控与自愈</p>
      <div class="features">
        <div class="feature-item">
          <h4>状态检测</h4>
          <p>组件健康检查</p>
        </div>
        <div class="feature-item">
          <h4>自动修复</h4>
          <p>故障自动恢复</p>
        </div>
        <div class="feature-item">
          <h4>性能监控</h4>
          <p>系统性能跟踪</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HealthCheckPlaceholder'
}
</script>

<style scoped>
.health-check-placeholder {
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