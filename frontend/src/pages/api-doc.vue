<template>
  <div>
    <h2>API 文档</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <div class="api-list">
        <div v-for="api in apis" :key="api.id" class="api-item" :class="{ missing: api.status !== 'available' }">
          <h3>{{ api.name }} <span v-if="api.api">({{ api.api }})</span></h3>
          <p>{{ api.desc }}</p>
          <div class="meta">
            <span class="category">{{ api.tags ? api.tags.join(', ') : '' }}</span>
            <span class="status" :class="api.status">
              {{ api.status === 'available' ? '🟢 已实现' : (api.status === 'script_only' ? '🟡 脚本' : '🔴 未实现') }}
            </span>
          </div>
          <div class="details">
            <span v-if="api.backend && api.backend.api">API: {{ api.backend.api }}</span>
            <span v-if="api.backend && api.backend.script">脚本: {{ api.backend.script }}</span>
            <span v-if="api.dag">DAG节点: {{ api.dag.node }}</span>
          </div>
        </div>
      </div>
      <div class="bubble-check">
        <h3>冒泡检测结果</h3>
        <p>未实现功能数量: {{ missingCount }}</p>
        <p v-if="missingCount === 0" style="color: green;">✅ 所有功能均已实现</p>
        <p v-else style="color: red;">❌ 有 {{ missingCount }} 个功能未实现</p>
        <p>完成度: {{ ((apis.length-missingCount)/apis.length*100).toFixed(1) }}%</p>
      </div>
    </div>
  </div>
  <ApiMapPanel />
  <ParamDeployPlaceholder />
</template>
<script>
import ApiMapPanel from '@/pages/api-map.vue'
import ParamDeployPlaceholder from '@/components/modules/ParamDeployPlaceholder.vue'

export default {
  name: 'ApiDocPage',
  components: {
    ApiMapPanel,
    ParamDeployPlaceholder
  },
  data() {
    return {
      apis: [],
      loading: true,
      error: null
    }
  },
  computed: {
    missingCount() {
      return this.apis.filter(api => !api.implemented).length;
    }
  },
  async mounted() {
    await this.loadApiDoc();
  },
  methods: {
    async loadApiDoc() {
      try {
        // 从统一接口映射表自动拉取所有功能项
        const response = await fetch('/api/docs');
        const text = await response.text();
        const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          let data = JSON.parse(jsonMatch[1]);
          // 自动补齐 tags 字段
          data = data.map(f => {
            let tags = [];
            if (f.api) tags.push('API');
            if (f.id && f.id.includes('ai')) tags.push('AI');
            if (f.status === 'script_only') tags.push('脚本');
            if (f.id && f.id.includes('dag')) tags.push('DAG');
            return { ...f, tags };
          });
          this.apis = data;
        } else {
          throw new Error('无法解析功能列表');
        }
      } catch (err) {
        this.error = '加载API文档失败: ' + err.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
<style scoped>
.api-list {
  margin-bottom: 20px;
}
.api-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.api-item.missing {
  border-color: #f44336;
  background-color: #ffebee;
}
.api-item h3 {
  margin: 0;
  font-size: 16px;
}
.api-item p {
  margin: 5px 0;
  color: #666;
}
.category {
  background-color: #2196F3;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.status.implemented {
  background-color: #4CAF50;
  color: white;
}
.status.missing {
  background-color: #f44336;
  color: white;
}
.bubble-check {
  border-top: 1px solid #ddd;
  padding-top: 20px;
}
</style>
