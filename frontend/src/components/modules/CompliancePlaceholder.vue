<template>
  <div class="compliance-placeholder">
    <h3>合规安全</h3>
    <div class="placeholder-content">
      <p>合规安全与风控日志</p>
      <div class="features">
        <div class="feature-item">
          <h4>合规检查</h4>
          <p>合规性验证</p>
        </div>
        <div class="feature-item">
          <h4>安全审计</h4>
          <p>安全日志审计</p>
        </div>
        <div class="feature-item">
          <h4>风控日志</h4>
          <p>风险控制日志</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CompliancePlaceholder'
}
</script>

<style scoped>
.compliance-placeholder {
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