<template>
  <div>
    <h2>接口映射表</h2>
    <div>
      <p>前端功能名称与后端API接口的完整映射，支持自然语言检索与跳转。</p>
      <table class="api-map-table">
        <thead>
          <tr>
            <th>功能名称</th>
            <th>描述</th>
            <th>API接口</th>
            <th>脚本</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in apiMap" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.desc }}</td>
            <td>{{ item.backend && item.backend.api }}</td>
            <td>{{ item.backend && item.backend.script }}</td>
            <td>{{ item.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const apiMap = ref([])
onMounted(async () => {
  const res = await fetch('/api/docs')
  const text = await res.text()
  const match = text.match(/```json([\s\S]*?)```/)
  if (match) {
    apiMap.value = JSON.parse(match[1]).functions || []
  }
})
</script>
<style scoped>
.api-map-table { width: 100%; border-collapse: collapse; }
.api-map-table th, .api-map-table td { border: 1px solid #ccc; padding: 6px 10px; }
.api-map-table th { background: #f5f5f5; }
</style>
