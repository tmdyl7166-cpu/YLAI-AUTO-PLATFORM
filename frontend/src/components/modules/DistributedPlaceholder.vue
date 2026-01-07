<template>
  <div class="distributed-placeholder">
    <h3>分布式采集</h3>
    <div class="placeholder-content">
      <p>分布式数据采集系统</p>
      <div class="features">
        <div class="feature-item">
          <h4>节点管理</h4>
          <p>分布式节点控制</p>
        </div>
        <div class="feature-item">
          <h4>负载均衡</h4>
          <p>任务负载分配</p>
        </div>
        <div class="feature-item">
          <h4>数据同步</h4>
          <p>跨节点数据同步</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DistributedPlaceholder'
}
</script>

<style scoped>
.distributed-placeholder {
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