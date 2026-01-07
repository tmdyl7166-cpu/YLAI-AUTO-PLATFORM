<template>
  <div class="data-mining-placeholder">
    <h3>数据挖掘</h3>
    <div class="placeholder-content">
      <p>数据分析与挖掘</p>
      <div class="features">
        <div class="feature-item">
          <h4>数据分析</h4>
          <p>统计分析与可视化</p>
        </div>
        <div class="feature-item">
          <h4>模式识别</h4>
          <p>数据模式发现</p>
        </div>
        <div class="feature-item">
          <h4>预测建模</h4>
          <p>数据预测分析</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DataMiningPlaceholder'
}
</script>

<style scoped>
.data-mining-placeholder {
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