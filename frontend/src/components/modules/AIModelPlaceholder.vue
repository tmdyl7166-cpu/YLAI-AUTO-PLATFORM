<template>
  <div class="ai-model-placeholder">
    <h3>AI模型训练</h3>
    <div class="placeholder-content">
      <p>AI模型训练与优化</p>
      <div class="features">
        <div class="feature-item">
          <h4>模型训练</h4>
          <p>自动化模型训练</p>
        </div>
        <div class="feature-item">
          <h4>参数调优</h4>
          <p>超参数优化</p>
        </div>
        <div class="feature-item">
          <h4>模型评估</h4>
          <p>性能评估与验证</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIModelPlaceholder'
}
</script>

<style scoped>
.ai-model-placeholder {
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