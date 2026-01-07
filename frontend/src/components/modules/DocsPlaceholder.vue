<template>
  <div class="docs-placeholder">
    <h3>文档管理</h3>
    <div class="placeholder-content">
      <p>文档与变更日志</p>
      <div class="features">
        <div class="feature-item">
          <h4>文档生成</h4>
          <p>自动化文档生成</p>
        </div>
        <div class="feature-item">
          <h4>版本控制</h4>
          <p>文档版本管理</p>
        </div>
        <div class="feature-item">
          <h4>变更日志</h4>
          <p>变更记录管理</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocsPlaceholder'
}
</script>

<style scoped>
.docs-placeholder {
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