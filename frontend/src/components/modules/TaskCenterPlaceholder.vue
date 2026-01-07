<template>
  <div class="task-center-placeholder">
    <h3>任务中心</h3>
    <div class="placeholder-content">
      <p>任务调度与管理中心</p>
      <div class="features">
        <div class="feature-item">
          <h4>任务队列</h4>
          <p>管理异步任务队列</p>
        </div>
        <div class="feature-item">
          <h4>调度器</h4>
          <p>定时任务调度</p>
        </div>
        <div class="feature-item">
          <h4>工作流</h4>
          <p>复杂任务编排</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskCenterPlaceholder'
}
</script>

<style scoped>
.task-center-placeholder {
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