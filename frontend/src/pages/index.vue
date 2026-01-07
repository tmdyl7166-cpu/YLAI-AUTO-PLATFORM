<template>
  <div class="index-page">
    <header class="header">
      <h2>{{ $t('index.title') }}</h2>
      <nav class="nav">
        <router-link to="/run" class="nav-link">{{ $t('nav.run') }}</router-link>
        <router-link to="/monitor" class="nav-link">{{ $t('nav.monitor') }}</router-link>
        <router-link to="/api-doc" class="nav-link">{{ $t('nav.apiDoc') }}</router-link>
        <router-link to="/visual-pipeline" class="nav-link">{{ $t('nav.visualPipeline') }}</router-link>
        <router-link to="/rbac" class="nav-link">{{ $t('nav.rbac') }}</router-link>
        <router-link to="/settings" class="nav-link">{{ $t('nav.settings') }}</router-link>
        <router-link to="/about" class="nav-link">{{ $t('nav.about') }}</router-link>
      </nav>
    </header>

    <main class="main-content">
      <TaskCenterPlaceholder>
        <ParamDeployPlaceholder />
        <SchedulerPlaceholder />
        <CollectTaskPlaceholder />
        <EnumTaskPlaceholder />
        <IdentifyTaskPlaceholder />
        <CrackTaskPlaceholder />
        <AutoStatusPlaceholder />
        <LogManagePlaceholder />
        <WorkflowDeployPlaceholder />
        <AdvancedFeaturePlaceholder />
        <SystemSettingsPlaceholder />
      </TaskCenterPlaceholder>

      <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="functions.length > 0" class="function-cards">
        <div
          v-for="func in sortedFunctions"
          :key="func.id"
          class="card"
          @click="navigateTo(func)"
        >
          <h3>{{ func.name }}</h3>
          <p>{{ func.desc }}</p>
          <div class="tags">
            <span v-for="tag in func.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <span :class="['status', func.status === 'available' ? 'available' : '']">
            {{ func.status === 'available' ? $t('index.available') : $t('index.unavailable') }}
          </span>
        </div>
      </div>
    </main>

    <router-view></router-view>
  </div>
</template>

<script>
import TaskCenterPlaceholder from '@/components/modules/TaskCenterPlaceholder.vue'
import ParamDeployPlaceholder from '@/components/modules/ParamDeployPlaceholder.vue'
import SchedulerPlaceholder from '@/components/modules/SchedulerPlaceholder.vue'
import CollectTaskPlaceholder from '@/components/modules/CollectTaskPlaceholder.vue'
import EnumTaskPlaceholder from '@/components/modules/EnumTaskPlaceholder.vue'
import IdentifyTaskPlaceholder from '@/components/modules/IdentifyTaskPlaceholder.vue'
import CrackTaskPlaceholder from '@/components/modules/CrackTaskPlaceholder.vue'
import AutoStatusPlaceholder from '@/components/modules/AutoStatusPlaceholder.vue'
import LogManagePlaceholder from '@/components/modules/LogManagePlaceholder.vue'
import WorkflowDeployPlaceholder from '@/components/modules/WorkflowDeployPlaceholder.vue'
import AdvancedFeaturePlaceholder from '@/components/modules/AdvancedFeaturePlaceholder.vue'
import SystemSettingsPlaceholder from '@/components/modules/SystemSettingsPlaceholder.vue'

export default {
  name: 'IndexPage',
  components: {
    TaskCenterPlaceholder,
    ParamDeployPlaceholder,
    SchedulerPlaceholder,
    CollectTaskPlaceholder,
    EnumTaskPlaceholder,
    IdentifyTaskPlaceholder,
    CrackTaskPlaceholder,
    AutoStatusPlaceholder,
    LogManagePlaceholder,
    WorkflowDeployPlaceholder,
    AdvancedFeaturePlaceholder,
    SystemSettingsPlaceholder
  },
  data() {
    return {
      functions: [],
      loading: true,
      error: null,
      sortBy: 'name' // 'name', 'status', 'tags'
    }
  },
  computed: {
    sortedFunctions() {
      return [...this.functions].sort((a, b) => {
        if (this.sortBy === 'status') {
          return a.status === 'available' ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      })
    }
  },
  async mounted() {
    await this.loadFunctions()
  },
  methods: {
    async loadFunctions() {
      try {
        const { apiClient } = await import('@/api/client')
        
        // 使用新的 apiClient，自动处理重试和标准响应格式
        const response = await apiClient.get('/api/functions')
        
        // response 已经是解析过的数据 (标准格式: code/message/data)
        let data = response?.data || response
        
        if (Array.isArray(data)) {
          this.functions = data.map(f => {
            const tags = []
            if (f.status === 'available') tags.push('可用')
            if (f.status === 'script_only') tags.push('脚本')
            if (f.id && f.id.includes('dag')) tags.push('DAG')
            return { ...f, tags }
          })
        } else {
          throw new Error('无法解析功能列表')
        }
      } catch (err) {
        this.error = '加载功能列表失败: ' + err.message
      } finally {
        this.loading = false
      }
    },
    navigateTo(func) {
      if (func.api) {
        this.$router.push({
          path: '/run',
          query: {
            id: func.id,
            name: func.name,
            api: func.api,
            desc: func.desc,
            status: func.status,
            tags: func.tags ? func.tags.join(',') : ''
          }
        })
      } else {
        this.$router.push({
          path: '/run',
          query: {
            id: func.id,
            name: func.name,
            script: func.id,
            desc: func.desc,
            status: func.status,
            tags: func.tags ? func.tags.join(',') : ''
          }
        })
      }
    }
  }
}
</script>

<style scoped>
.index-page {
  min-height: 100vh;
  font-family: 'Arial', sans-serif;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
}

.nav {
  margin-top: 20px;
}

.nav-link {
  color: white;
  text-decoration: none;
  margin: 0 15px;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
}

.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading, .error {
  text-align: center;
  padding: 20px;
  font-size: 18px;
}

.error {
  color: #f44336;
}

.function-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card h3 {
  margin-top: 0;
  color: #333;
}

.card p {
  color: #666;
  margin: 10px 0;
}

.tags {
  margin: 10px 0;
}

.tag {
  display: inline-block;
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  margin-right: 5px;
  margin-bottom: 5px;
}

.status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status.available {
  background-color: #4CAF50;
  color: white;
}

.status:not(.available) {
  background-color: #f44336;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .function-cards {
    grid-template-columns: 1fr;
  }

  .nav-link {
    display: block;
    margin: 5px 0;
  }
}
</style>
