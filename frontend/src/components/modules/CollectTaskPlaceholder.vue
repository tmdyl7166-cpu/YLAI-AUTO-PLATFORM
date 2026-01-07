<template>
  <div class="collect-task-placeholder">
    <h3>采集任务</h3>
    <div class="placeholder-content">
      <p>数据采集任务管理</p>
      <div class="features">
        <div class="feature-item">
          <h4>任务配置</h4>
          <p>采集任务参数设置</p>
        </div>
        <div class="feature-item">
          <h4>执行监控</h4>
          <p>任务执行状态监控</p>
        </div>
        <div class="feature-item">
          <h4>结果处理</h4>
          <p>采集结果数据处理</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CollectTaskPlaceholder'
}
</script>

<style scoped>
.collect-task-placeholder {
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