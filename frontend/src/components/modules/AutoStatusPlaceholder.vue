<template>
  <div class="auto-status-placeholder">
    <h3>自动化状态</h3>
    <div class="placeholder-content">
      <p>自动化流程状态监控</p>
      <div class="features">
        <div class="feature-item">
          <h4>流程监控</h4>
          <p>自动化流程执行状态</p>
        </div>
        <div class="feature-item">
          <h4>状态报告</h4>
          <p>执行结果统计</p>
        </div>
        <div class="feature-item">
          <h4>异常处理</h4>
          <p>自动化异常恢复</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AutoStatusPlaceholder'
}
</script>

<style scoped>
.auto-status-placeholder {
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