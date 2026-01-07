<template>
  <div class="log-manage-placeholder">
    <h3>日志管理</h3>
    <div class="placeholder-content">
      <p>系统日志收集与管理</p>
      <div class="features">
        <div class="feature-item">
          <h4>日志收集</h4>
          <p>多源日志聚合</p>
        </div>
        <div class="feature-item">
          <h4>日志分析</h4>
          <p>日志内容分析</p>
        </div>
        <div class="feature-item">
          <h4>日志存储</h4>
          <p>日志持久化存储</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogManagePlaceholder'
}
</script>

<style scoped>
.log-manage-placeholder {
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