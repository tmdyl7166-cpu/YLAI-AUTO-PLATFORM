<template>
  <div class="enum-task-placeholder">
    <h3>枚举任务</h3>
    <div class="placeholder-content">
      <p>目标枚举与发现</p>
      <div class="features">
        <div class="feature-item">
          <h4>目标扫描</h4>
          <p>网络目标发现</p>
        </div>
        <div class="feature-item">
          <h4>端口枚举</h4>
          <p>服务端口识别</p>
        </div>
        <div class="feature-item">
          <h4>服务识别</h4>
          <p>运行服务检测</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EnumTaskPlaceholder'
}
</script>

<style scoped>
.enum-task-placeholder {
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