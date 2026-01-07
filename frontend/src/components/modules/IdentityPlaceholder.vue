<template>
  <div class="identity-placeholder">
    <h3>身份伪造</h3>
    <div class="placeholder-content">
      <p>身份伪造与无痕采集</p>
      <div class="features">
        <div class="feature-item">
          <h4>身份生成</h4>
          <p>虚拟身份创建</p>
        </div>
        <div class="feature-item">
          <h4>指纹伪造</h4>
          <p>浏览器指纹伪装</p>
        </div>
        <div class="feature-item">
          <h4>行为模拟</h4>
          <p>人类行为模拟</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IdentityPlaceholder'
}
</script>

<style scoped>
.identity-placeholder {
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