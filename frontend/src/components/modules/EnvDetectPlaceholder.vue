<template>
  <div class="env-detect-placeholder">
    <h3>环境检测</h3>
    <div class="placeholder-content">
      <p>环境检测与依赖管理</p>
      <div class="features">
        <div class="feature-item">
          <h4>环境扫描</h4>
          <p>系统环境检测</p>
        </div>
        <div class="feature-item">
          <h4>依赖检查</h4>
          <p>依赖完整性验证</p>
        </div>
        <div class="feature-item">
          <h4>兼容性测试</h4>
          <p>版本兼容性检查</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EnvDetectPlaceholder'
}
</script>

<style scoped>
.env-detect-placeholder {
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