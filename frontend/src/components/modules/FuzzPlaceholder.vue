<template>
  <div class="fuzz-placeholder">
    <h3>Fuzz测试</h3>
    <div class="placeholder-content">
      <p>模糊测试与参数变异</p>
      <div class="features">
        <div class="feature-item">
          <h4>参数生成</h4>
          <p>智能参数变异</p>
        </div>
        <div class="feature-item">
          <h4>漏洞检测</h4>
          <p>安全漏洞发现</p>
        </div>
        <div class="feature-item">
          <h4>边界测试</h4>
          <p>极限条件测试</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FuzzPlaceholder'
}
</script>

<style scoped>
.fuzz-placeholder {
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