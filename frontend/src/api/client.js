/**
 * 统一的前端 API 客户端 (v1.1)
 * 
 * 提供：
 * - 统一的 HTTP 请求方法（GET/POST/PUT/DELETE 等）
 * - 自动错误处理与重试
 * - 请求/响应拦截
 * - 超时控制
 * - 认证令牌管理
 * - 标准 API 响应格式处理
 * 
 * 使用示例:
 *   import { apiClient } from '@/api/client'
 *   const response = await apiClient.get('/health')
 *   const data = await apiClient.post('/tasks', { name: 'my-task' })
 */

import axios from 'axios'

// 获取 API 基础 URL（支持环境变量）
const getApiBase = () => {
  // 优先使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 开发环境使用代理
  if (import.meta.env.DEV) {
    return '/api'
  }
  // 生产环境使用完整 URL
  const protocol = window.location.protocol
  const host = window.location.hostname
  const port = 8001
  return `${protocol}//${host}:${port}/api`
}

const API_BASE = getApiBase()
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000
const RETRY_TIMES = parseInt(import.meta.env.VITE_REQUEST_RETRY_TIMES) || 3
const RETRY_DELAY = parseInt(import.meta.env.VITE_REQUEST_RETRY_DELAY) || 1000

// 创建 axios 实例
const client = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 重试逻辑：处理临时性错误（超时、网络错误等）
 */
async function withRetry(fn, retries = RETRY_TIMES, delay = RETRY_DELAY) {
  let lastError
  
  for (let i = 0; i < retries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      
      // 判断是否应该重试
      const shouldRetry =
        error.code === 'ECONNABORTED' || // 超时
        error.code === 'ENOTFOUND' || // DNS 错误
        error.response?.status >= 500 || // 服务端错误
        !error.response // 网络错误
      
      if (!shouldRetry || i === retries - 1) {
        break
      }
      
      // 指数退避延迟
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
  
  throw lastError
}

// 请求拦截器
client.interceptors.request.use(
  config => {
    // 添加认证令牌（如果存在）
    const token = localStorage.getItem(import.meta.env.VITE_TOKEN_STORAGE_KEY || 'auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一处理响应与错误
client.interceptors.response.use(
  response => {
    const { data } = response
    
    // 检查标准 API 响应格式（code + message + data）
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) {
        // 成功响应，返回数据
        return data
      } else {
        // API 业务错误
        const error = new Error(data.message || 'API Error')
        error.code = data.code
        error.response = data
        return Promise.reject(error)
      }
    }
    
    // 非标准响应（用于兼容性）
    return data
  },
  error => {
    // 处理 HTTP 错误
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        // 认证失败，清除令牌并重定向到登录
        localStorage.removeItem(import.meta.env.VITE_TOKEN_STORAGE_KEY || 'auth_token')
        window.location.href = '/login'
      } else if (status === 403) {
        // 权限不足
        console.error('权限不足:', data?.message)
      } else if (status >= 500) {
        // 服务器错误
        console.error('服务器错误:', data?.message)
      }
      
      error.message = data?.message || `HTTP ${status}`
    } else if (error.request) {
      // 请求已发送但无响应
      error.message = 'Network error - no response from server'
    } else {
      // 请求配置错误
      error.message = error.message || 'Request setup error'
    }
    
    return Promise.reject(error)
  }
)

/**
 * 统一的 API 客户端对象
 */
export const apiClient = {
  /**
   * GET 请求
   */
  get(url, config = {}) {
    return withRetry(() => client.get(url, config))
  },

  /**
   * POST 请求
   */
  post(url, data = {}, config = {}) {
    return withRetry(() => client.post(url, data, config))
  },

  /**
   * PUT 请求
   */
  put(url, data = {}, config = {}) {
    return withRetry(() => client.put(url, data, config))
  },

  /**
   * PATCH 请求
   */
  patch(url, data = {}, config = {}) {
    return withRetry(() => client.patch(url, data, config))
  },

  /**
   * DELETE 请求
   */
  delete(url, config = {}) {
    return withRetry(() => client.delete(url, config))
  },

  /**
   * 获取 axios 原始实例（用于高级用法）
   */
  getAxios() {
    return client
  },

  /**
   * 设置全局请求头
   */
  setHeader(key, value) {
    client.defaults.headers[key] = value
  },

  /**
   * 移除全局请求头
   */
  removeHeader(key) {
    delete client.defaults.headers[key]
  },
}

/**
 * 业务 API 调用方法（保留以兼容现有代码）
 */
export const api = {
  // 获取健康检查
  getHealth() {
    return apiClient.get('/health')
  },

  // 获取系统信息
  getSystemInfo() {
    return apiClient.get('/system/info')
  },

  // 获取所有可用脚本
  getScripts() {
    return apiClient.get('/scripts')
  },

  // 执行脚本
  runScript(scriptId, params = {}) {
    return apiClient.post(`/scripts/${scriptId}/run`, { params })
  },

  // 获取任务列表
  getTasks(filter = {}) {
    return apiClient.get('/tasks', { params: filter })
  },

  // 创建新任务
  createTask(taskData) {
    return apiClient.post('/tasks', taskData)
  },

  // 获取任务详情
  getTask(taskId) {
    return apiClient.get(`/tasks/${taskId}`)
  },

  // 更新任务
  updateTask(taskId, taskData) {
    return apiClient.put(`/tasks/${taskId}`, taskData)
  },

  // 删除任务
  deleteTask(taskId) {
    return apiClient.delete(`/tasks/${taskId}`)
  },

  // 执行任务
  runTask(taskId) {
    return apiClient.post(`/tasks/${taskId}/run`)
  },

  // 停止任务
  stopTask(taskId) {
    return apiClient.post(`/tasks/${taskId}/stop`)
  },

  // 获取管道列表
  getPipelines(filter = {}) {
    return apiClient.get('/pipeline', { params: filter })
  },

  // 创建管道
  createPipeline(pipelineData) {
    return apiClient.post('/pipeline', pipelineData)
  },

  // 执行管道
  runPipeline(pipelineId) {
    return apiClient.post(`/pipeline/${pipelineId}/run`)
  },

  // 获取监控信息
  getMonitoring() {
    return apiClient.get('/monitor')
  },

  // 获取日志
  getLogs(filter = {}) {
    return apiClient.get('/logs', { params: filter })
  },

  // 获取插件列表
  getPlugins() {
    return apiClient.get('/plugins')
  },

  // 安装插件
  installPlugin(pluginData) {
    return apiClient.post('/plugins', pluginData)
  },

  // 卸载插件
  uninstallPlugin(pluginId) {
    return apiClient.delete(`/plugins/${pluginId}`)
  },
}

// 导出默认客户端
export default apiClient
    return client.get(`/tasks/${taskId}`)
  },

  // 更新任务
  updateTask(taskId, taskData) {
    return client.put(`/tasks/${taskId}`, taskData)
  },

  // 删除任务
  deleteTask(taskId) {
    return client.delete(`/tasks/${taskId}`)
  },

  // 获取监控指标
  getMetrics() {
    return client.get('/metrics')
  },

  // 获取日志
  getLogs(filter = {}) {
    return client.get('/logs', { params: filter })
  },

  // 获取 DAG 流水线
  getPipelines() {
    return client.get('/pipelines')
  },

  // 创建 DAG 流水线
  createPipeline(pipelineData) {
    return client.post('/pipelines', pipelineData)
  },

  // 运行 DAG 流水线
  runPipeline(pipelineId) {
    return client.post(`/pipelines/${pipelineId}/run`)
  },

  // 获取用户列表
  getUsers() {
    return client.get('/users')
  },

  // 获取角色列表
  getRoles() {
    return client.get('/roles')
  },

  // 获取权限
  getPermissions() {
    return client.get('/permissions')
  },

  // 获取系统设置
  getSettings() {
    return client.get('/settings')
  },

  // 更新系统设置
  updateSettings(settings) {
    return client.put('/settings', settings)
  }
}

export default client
