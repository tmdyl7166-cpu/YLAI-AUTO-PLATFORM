<template>
  <div class="phone-panel">
    <h3>📞 号码逆向分析</h3>
    <div class="input-section">
      <input
        v-model="phoneNumber"
        type="text"
        placeholder="输入手机号码"
        class="phone-input"
      >
      <button @click="analyzePhone" class="analyze-btn" :disabled="loading">
        {{ loading ? '分析中...' : '开始分析' }}
      </button>
    </div>

    <div v-if="result" class="result-section">
      <h4>分析结果</h4>
      <div class="result-card">
        <p><strong>号码:</strong> {{ result.phone }}</p>
        <p><strong>运营商:</strong> {{ result.carrier }}</p>
        <p><strong>省份:</strong> {{ result.province }}</p>
        <p><strong>城市:</strong> {{ result.city }}</p>
        <p><strong>区号:</strong> {{ result.area_code }}</p>
        <p><strong>邮编:</strong> {{ result.post_code }}</p>
      </div>
    </div>

    <div v-if="error" class="error-section">
      <p class="error-message">{{ error }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PhonePanel',
  data() {
    return {
      phoneNumber: '',
      result: null,
      error: null,
      loading: false
    }
  },
  methods: {
    async analyzePhone() {
      if (!this.phoneNumber.trim()) {
        this.error = '请输入手机号码';
        return;
      }

      this.loading = true;
      this.error = null;
      this.result = null;

      try {
        const response = await fetch('/api/phone/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            phone: this.phoneNumber
          })
        });

        const data = await response.json();

        if (data.status === 'success') {
          this.result = data.data;
        } else {
          this.error = data.error || '分析失败';
        }
      } catch (err) {
        this.error = '网络错误，请重试';
        console.error('Phone analysis error:', err);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.phone-panel {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.input-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.phone-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.analyze-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.analyze-btn:hover:not(:disabled) {
  background: #0056b3;
}

.analyze-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.result-section, .error-section {
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
</style>