<template>
  <div class="demo-panel">
    <h3>🎯 模块化示例</h3>
    <div class="input-section">
      <input
        v-model="message"
        type="text"
        placeholder="输入消息"
        class="message-input"
      >
      <button @click="runDemo" class="run-btn" :disabled="loading">
        {{ loading ? '运行中...' : '运行示例' }}
      </button>
    </div>

    <div v-if="result" class="result-section">
      <h4>执行结果</h4>
      <div class="result-card">
        <p><strong>原始消息:</strong> {{ result.echo }}</p>
        <p><strong>长度:</strong> {{ result.length }}</p>
        <p><strong>大写:</strong> {{ result.upper }}</p>
        <p><strong>小写:</strong> {{ result.lower }}</p>
      </div>
    </div>

    <div v-if="error" class="error-section">
      <p class="error-message">{{ error }}</p>
    </div>

    <div class="description">
      <h4>功能说明</h4>
      <p>这是一个模块化示例，演示前后端API调用的完整流程。</p>
      <ul>
        <li>前端Vue组件处理用户输入</li>
        <li>通过API调用后端Python脚本</li>
        <li>后端脚本处理数据并返回结果</li>
        <li>前端展示处理结果</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DemoPanel',
  data() {
    return {
      message: 'Hello, YeLing!',
      result: null,
      error: null,
      loading: false
    }
  },
  methods: {
    async runDemo() {
      if (!this.message.trim()) {
        this.error = '请输入消息';
        return;
      }

      this.loading = true;
      this.error = null;
      this.result = null;

      try {
        const response = await fetch('/api/demo/run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: this.message
          })
        });

        const data = await response.json();

        if (data.status === 'success') {
          this.result = data.data;
        } else {
          this.error = data.error || '执行失败';
        }
      } catch (err) {
        this.error = '网络错误，请重试';
        console.error('Demo run error:', err);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.demo-panel {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.input-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.message-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.run-btn {
  padding: 10px 20px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.run-btn:hover:not(:disabled) {
  background: #218838;
}

.run-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.result-section, .error-section, .description {
  margin-top: 20px;
}

.result-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid #28a745;
}

.result-card p {
  margin: 5px 0;
}

.error-message {
  color: #dc3545;
  background: #f8d7da;
  padding: 10px;
  border-radius: 4px;
  border-left: 4px solid #dc3545;
}

.description {
  background: #e9ecef;
  padding: 15px;
  border-radius: 4px;
}

.description ul {
  margin: 10px 0 0 20px;
}

.description li {
  margin: 5px 0;
}
</style>