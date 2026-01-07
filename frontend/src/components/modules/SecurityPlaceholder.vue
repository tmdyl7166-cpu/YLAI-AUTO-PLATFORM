<template>
  <div class="security-placeholder">
    <h3>安全管理</h3>
    <div class="placeholder-content">
      <p>系统安全配置与管理</p>
      <div class="features">
        <div class="feature-item">
          <h4>访问控制</h4>
          <p>用户权限管理</p>
        </div>
        <div class="feature-item">
          <h4>加密配置</h4>
          <p>数据加密设置</p>
        </div>
        <div class="feature-item">
          <h4>审计日志</h4>
          <p>操作日志记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SecurityPlaceholder'
}
</script>

<style scoped>
.security-placeholder {
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