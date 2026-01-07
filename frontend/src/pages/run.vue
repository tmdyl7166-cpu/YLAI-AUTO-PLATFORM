<template>
  <div class="run-page">
    <header class="header">
      <h2>运行任务中心</h2>
      <button @click="clearCache" class="clear-cache-btn">清理缓存</button>
    </header>

    <div class="content">
      <AiDemoPanel />
      <ParamDeployPlaceholder />
      <CollectTaskPlaceholder />
      <IdentifyTaskPlaceholder />
      <CrackTaskPlaceholder />

      <div class="task-form-container">
        <h3>创建新任务</h3>
        <form @submit.prevent="runTask" class="task-form">
          <div v-if="funcMeta.script" class="form-group">
            <label for="script-select">脚本:</label>
            <select id="script-select" v-model="selectedScript" required class="form-control">
              <option value="">选择脚本</option>
              <option v-for="script in availableScripts" :key="script" :value="script">{{ script }}</option>
            </select>
          </div>

          <div v-if="funcMeta.schema && funcMeta.schema.length" class="params-section">
            <h4>参数配置</h4>
            <div v-for="param in funcMeta.schema" :key="param.name" class="param-item">
              <label :for="'param-' + param.name">{{ param.name }}:</label>
              <input
                :id="'param-' + param.name"
                v-model="param.value"
                :type="getInputType(param.type)"
                :placeholder="param.placeholder || ''"
                :required="param.required"
                class="form-control"
                @input="validateParam(param)"
              />
              <span v-if="param.error" class="error-message">{{ param.error }}</span>
            </div>
          </div>

          <div v-else class="form-group">
            <label for="params-json">参数 (JSON):</label>
            <textarea
              id="params-json"
              v-model="paramsJson"
              placeholder='{"key": "value"}'
              class="form-control"
              rows="5"
              @input="validateJson"
            ></textarea>
            <span v-if="jsonError" class="error-message">{{ jsonError }}</span>
          </div>

          <div class="form-actions">
            <button type="submit" :disabled="running || !isFormValid" class="btn btn-primary">
              <span v-if="running">运行中...</span>
              <span v-else>运行任务</span>
            </button>
            <button type="button" @click="resetForm" class="btn btn-secondary">重置</button>
          </div>
        </form>
      </div>

      <div v-if="lastResult" class="task-results">
        <h3>执行结果</h3>
        <div class="result-content">
          <pre>{{ JSON.stringify(lastResult, null, 2) }}</pre>
        </div>
        <button @click="copyResult" class="btn btn-secondary">复制结果</button>
      </div>

      <!-- 嵌套弹窗示例 -->
      <div v-if="showModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>{{ modalTitle }}</h3>
            <button @click="closeModal" class="close-btn">&times;</button>
          </div>
          <div class="modal-body">
            <p>{{ modalMessage }}</p>
            <button @click="confirmAction" class="btn btn-primary">确认</button>
            <button @click="closeModal" class="btn btn-secondary">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AiDemoPanel from '@/pages/ai-demo.vue'
import ParamDeployPlaceholder from '@/components/modules/ParamDeployPlaceholder.vue'
import CollectTaskPlaceholder from '@/components/modules/CollectTaskPlaceholder.vue'
import IdentifyTaskPlaceholder from '@/components/modules/IdentifyTaskPlaceholder.vue'
import CrackTaskPlaceholder from '@/components/modules/CrackTaskPlaceholder.vue'

export default {
  name: 'RunPage',
  components: {
    AiDemoPanel,
    ParamDeployPlaceholder,
    CollectTaskPlaceholder,
    IdentifyTaskPlaceholder,
    CrackTaskPlaceholder
  },
  data() {
    return {
      availableScripts: [],
      selectedScript: '',
      paramsJson: '',
      jsonError: '',
      running: false,
      lastResult: null,
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      confirmCallback: null,
      funcMeta: {
        id: '',
        name: '',
        api: '',
        script: '',
        desc: '',
        status: '',
        tags: [],
        schema: []
      }
    }
  },
  computed: {
    isFormValid() {
      if (this.funcMeta.script && !this.selectedScript) return false
      if (this.funcMeta.schema && this.funcMeta.schema.length) {
        return this.funcMeta.schema.every(p => !p.error && (p.required ? p.value : true))
      }
      return !this.jsonError
    }
  },
  async mounted() {
    await this.loadScripts()
    this.initFromQuery()
  },
  methods: {
    async loadScripts() {
      try {
        const response = await fetch('/api/scripts')
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data = await response.json()
        this.availableScripts = data.data || []
      } catch (err) {
        console.error('加载脚本列表失败:', err)
        this.showModalMessage('错误', '加载脚本列表失败: ' + err.message)
      }
    },
    initFromQuery() {
      const query = this.$route.query || {}
      this.funcMeta = {
        id: query.id || '',
        name: query.name || '',
        api: query.api || '',
        script: query.script || '',
        desc: query.desc || '',
        status: query.status || '',
        tags: query.tags ? query.tags.split(',') : [],
        schema: []
      }
      this.loadSchema()
      if (this.funcMeta.script) {
        this.selectedScript = this.funcMeta.script
      }
    },
    async loadSchema() {
      try {
        const resp = await fetch('/api/docs')
        const text = await resp.text()
        const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/)
        if (jsonMatch) {
          const data = JSON.parse(jsonMatch[1])
          const found = data.find(f => f.id === this.funcMeta.id)
          if (found && found.schema) {
            this.funcMeta.schema = found.schema.map(p => ({ ...p, value: '', error: '' }))
          }
        }
      } catch (err) {
        console.warn('加载schema失败:', err)
      }
    },
    getInputType(type) {
      const typeMap = {
        'string': 'text',
        'number': 'number',
        'boolean': 'checkbox',
        'email': 'email',
        'url': 'url'
      }
      return typeMap[type] || 'text'
    },
    validateParam(param) {
      param.error = ''
      if (param.required && !param.value) {
        param.error = '此字段为必填项'
      } else if (param.type === 'email' && param.value && !/\S+@\S+\.\S+/.test(param.value)) {
        param.error = '请输入有效的邮箱地址'
      } else if (param.type === 'url' && param.value && !/^https?:\/\/.+/.test(param.value)) {
        param.error = '请输入有效的URL'
      }
    },
    validateJson() {
      this.jsonError = ''
      if (this.paramsJson.trim()) {
        try {
          JSON.parse(this.paramsJson)
        } catch (e) {
          this.jsonError = 'JSON格式错误: ' + e.message
        }
      }
    },
    async runTask() {
      if (!this.isFormValid) return

      this.running = true
      try {
        let params = {}
        if (this.funcMeta.schema && this.funcMeta.schema.length) {
          this.funcMeta.schema.forEach(p => {
            params[p.name] = p.value
          })
        } else if (this.paramsJson.trim()) {
          params = JSON.parse(this.paramsJson)
        }

        let result = null
        if (this.funcMeta.api) {
          const response = await fetch(this.funcMeta.api, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
          })
          if (!response.ok) throw new Error(`API调用失败: ${response.status}`)
          result = await response.json()
        } else if (this.selectedScript) {
          const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              script: this.selectedScript,
              params: params
            })
          })
          if (!response.ok) throw new Error(`脚本调用失败: ${response.status}`)
          result = await response.json()
        } else {
          throw new Error('未指定API或脚本')
        }
        this.lastResult = result
        this.showModalMessage('成功', '任务执行完成')
      } catch (err) {
        this.lastResult = { error: err.message }
        this.showModalMessage('错误', '任务执行失败: ' + err.message)
      } finally {
        this.running = false
      }
    },
    resetForm() {
      this.selectedScript = ''
      this.paramsJson = ''
      this.jsonError = ''
      this.funcMeta.schema.forEach(p => {
        p.value = ''
        p.error = ''
      })
      this.lastResult = null
    },
    clearCache() {
      if ('caches' in window) {
        caches.keys().then(names => {
          names.forEach(name => {
            caches.delete(name)
          })
        })
      }
      localStorage.clear()
      sessionStorage.clear()
      this.showModalMessage('成功', '缓存已清理')
    },
    copyResult() {
      navigator.clipboard.writeText(JSON.stringify(this.lastResult, null, 2))
      this.showModalMessage('成功', '结果已复制到剪贴板')
    },
    showModalMessage(title, message) {
      this.modalTitle = title
      this.modalMessage = message
      this.showModal = true
      this.confirmCallback = null
    },
    closeModal() {
      this.showModal = false
      this.modalTitle = ''
      this.modalMessage = ''
      this.confirmCallback = null
    },
    confirmAction() {
      if (this.confirmCallback) {
        this.confirmCallback()
      }
      this.closeModal()
    }
  }
}
</script>

<style scoped>
.run-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-cache-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.clear-cache-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.task-form-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.task-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.error-message {
  color: #f44336;
  font-size: 12px;
  margin-top: 5px;
}

.params-section {
  margin-top: 20px;
}

.param-item {
  margin-bottom: 15px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a67d8;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #cbd5e0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.task-results {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.result-content pre {
  background: #f7fafc;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 0;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #a0aec0;
}

.modal-body {
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 10px;
  }

  .form-actions {
    flex-direction: column;
  }

  .modal-content {
    width: 95%;
  }
}
</style>
