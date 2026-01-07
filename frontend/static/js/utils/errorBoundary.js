import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './stores/auth'
import { useNotificationStore } from './stores/notification'

// 错误边界组件
const ErrorBoundary = {
  name: 'ErrorBoundary',
  data() {
    return {
      hasError: false,
      error: null
    }
  },
  errorCaptured(err, instance, info) {
    this.hasError = true
    this.error = err
    console.error('Error captured:', err, info)
    // 报告错误到监控系统
    this.reportError(err, info)
    return false
  },
  methods: {
    reportError(error, info) {
      // 发送错误到后端监控
      axios.post('/api/errors', {
        message: error.message,
        stack: error.stack,
        info,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      }).catch(console.error)
    },
    resetError() {
      this.hasError = false
      this.error = null
    }
  },
  render() {
    if (this.hasError) {
      return this.$createElement('div', {
        class: 'error-boundary'
      }, [
        this.$createElement('h2', '出错了'),
        this.$createElement('p', this.error?.message || '未知错误'),
        this.$createElement('button', {
          on: { click: this.resetError }
        }, '重试')
      ])
    }
    return this.$slots.default?.[0]
  }
}

// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error)
  // 报告错误
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  // 报告错误
})

// 应用初始化
export function createMainApp() {
  const app = createApp(App)

  // 安装错误边界
  app.component('ErrorBoundary', ErrorBoundary)

  // 全局错误处理
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue error:', err, info)
    // 报告错误到监控系统
    const notificationStore = useNotificationStore()
    notificationStore.addNotification({
      type: 'error',
      title: '应用错误',
      message: err.message,
      duration: 5000
    })
  }

  // 性能监控
  app.mixin({
    beforeCreate() {
      this.$startTime = performance.now()
    },
    mounted() {
      const loadTime = performance.now() - this.$startTime
      if (loadTime > 100) { // 超过100ms记录
        console.warn(`${this.$options.name || 'Component'} 加载时间: ${loadTime.toFixed(2)}ms`)
      }
    }
  })

  return app
}