<template>
  <div class="system-settings-placeholder">
    <h3>系统设置</h3>
    <div class="placeholder-content">
      <p>系统配置与设置</p>
      <div class="features">
        <div class="feature-item">
          <h4>基础配置</h4>
          <p>系统基础参数</p>
        </div>
        <div class="feature-item">
          <h4>高级设置</h4>
          <p>高级功能配置</p>
        </div>
        <div class="feature-item">
          <h4>维护工具</h4>
          <p>系统维护功能</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemSettingsPlaceholder'
}
</script>

<style scoped>
.system-settings-placeholder {
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