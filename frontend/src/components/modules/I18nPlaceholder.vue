<template>
  <div class="i18n-placeholder">
    <h3>国际化</h3>
    <div class="placeholder-content">
      <p>国际化与本地化</p>
      <div class="features">
        <div class="feature-item">
          <h4>多语言支持</h4>
          <p>界面多语言切换</p>
        </div>
        <div class="feature-item">
          <h4>本地化适配</h4>
          <p>地区化内容适配</p>
        </div>
        <div class="feature-item">
          <h4>翻译管理</h4>
          <p>翻译内容管理</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'I18nPlaceholder'
}
</script>

<style scoped>
.i18n-placeholder {
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