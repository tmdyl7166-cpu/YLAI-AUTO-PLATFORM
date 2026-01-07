<template>
  <div class="identify-task-placeholder">
    <h3>身份识别</h3>
    <div class="placeholder-content">
      <p>身份验证与识别</p>
      <div class="features">
        <div class="feature-item">
          <h4>凭证管理</h4>
          <p>身份凭证存储</p>
        </div>
        <div class="feature-item">
          <h4>认证测试</h4>
          <p>身份验证测试</p>
        </div>
        <div class="feature-item">
          <h4>权限评估</h4>
          <p>访问权限评估</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IdentifyTaskPlaceholder'
}
</script>

<style scoped>
.identify-task-placeholder {
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