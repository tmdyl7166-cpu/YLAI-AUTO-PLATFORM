<template>
  <div class="performance-placeholder">
    <h3>性能管理</h3>
    <div class="placeholder-content">
      <p>性能与资源管理</p>
      <div class="features">
        <div class="feature-item">
          <h4>资源监控</h4>
          <p>系统资源监控</p>
        </div>
        <div class="feature-item">
          <h4>性能优化</h4>
          <p>性能瓶颈优化</p>
        </div>
        <div class="feature-item">
          <h4>负载均衡</h4>
          <p>资源负载均衡</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PerformancePlaceholder'
}
</script>

<style scoped>
.performance-placeholder {
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