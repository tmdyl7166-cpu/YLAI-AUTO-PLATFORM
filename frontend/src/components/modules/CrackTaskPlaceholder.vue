<template>
  <div class="crack-task-placeholder">
    <h3>破解任务</h3>
    <div class="placeholder-content">
      <p>密码破解与安全测试</p>
      <div class="features">
        <div class="feature-item">
          <h4>密码破解</h4>
          <p>密码暴力破解</p>
        </div>
        <div class="feature-item">
          <h4>字典攻击</h4>
          <p>基于字典的攻击</p>
        </div>
        <div class="feature-item">
          <h4>安全评估</h4>
          <p>密码强度评估</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CrackTaskPlaceholder'
}
</script>

<style scoped>
.crack-task-placeholder {
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