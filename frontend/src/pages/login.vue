<template>
  <div class="login-container">
    <div class="login-form">
      <h2>系统登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="credentials.username"
            type="text"
            required
            placeholder="请输入用户名"
          >
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="credentials.password"
            type="password"
            required
            placeholder="请输入密码"
          >
        </div>
        <div class="form-group">
          <label>
            <input
              v-model="credentials.remember"
              type="checkbox"
            >
            记住我
          </label>
        </div>
        <button type="submit" :disabled="loading" class="login-btn">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <div v-if="error" class="error-message">{{ error }}</div>
      <div class="login-footer">
        <p>忘记密码？<a href="#" @click.prevent="forgotPassword">点击重置</a></p>
        <p>没有账号？<a href="#" @click.prevent="register">立即注册</a></p>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'LoginPage',
  data() {
    return {
      credentials: {
        username: '',
        password: '',
        remember: false
      },
      loading: false,
      error: null
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = null;
      try {
        // 模拟登录API调用
        await new Promise(resolve => setTimeout(resolve, 1000));
        // 这里应该调用实际的登录API
        if (this.credentials.username === 'admin' && this.credentials.password === 'admin') {
          // 登录成功，跳转到首页
          this.$router.push('/');
          // 这里可以设置token等
          localStorage.setItem('token', 'fake-token');
        } else {
          throw new Error('用户名或密码错误');
        }
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    forgotPassword() {
      alert('忘记密码功能开发中，请联系管理员');
    },
    register() {
      alert('注册功能开发中，请联系管理员');
    }
  }
}
</script>
<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}
.login-form {
  background-color: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}
.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #555;
  font-weight: 500;
}
.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}
.form-group input[type="checkbox"] {
  margin-right: 8px;
}
.login-btn {
  width: 100%;
  padding: 12px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.login-btn:hover:not(:disabled) {
  background-color: #1976D2;
}
.login-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
.error-message {
  color: #f44336;
  text-align: center;
  margin-top: 15px;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 4px;
}
.login-footer {
  text-align: center;
  margin-top: 20px;
}
.login-footer p {
  margin: 5px 0;
  color: #666;
}
.login-footer a {
  color: #2196F3;
  text-decoration: none;
}
.login-footer a:hover {
  text-decoration: underline;
}
</style>
