<template>
  <div class="param-deploy-placeholder">
    <h3>参数部署</h3>
    <div class="placeholder-content">
      <p>动态参数配置与部署</p>
      <div class="features">
        <div class="feature-item">
          <h4>参数模板</h4>
          <p>预定义参数配置</p>
        </div>
        <div class="feature-item">
          <h4>环境变量</h4>
          <p>多环境参数管理</p>
        </div>
        <div class="feature-item">
          <h4>热更新</h4>
          <p>运行时参数调整</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ParamDeployPlaceholder'
}
</script>

<style scoped>
.param-deploy-placeholder {
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