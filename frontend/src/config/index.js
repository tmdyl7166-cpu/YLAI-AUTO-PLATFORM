/**
 * 全局配置常量
 */

// API 服务器配置
export const API_CONFIG = {
  // 开发环境
  dev: {
    protocol: 'http',
    host: 'localhost',
    port: 8001,
    apiPath: '/api'
  },
  // 生产环境
  prod: {
    protocol: window.location.protocol.replace(':', ''),
    host: window.location.hostname,
    port: 8001,
    apiPath: '/api'
  }
}

// 根据环境获取配置
export const getConfig = () => {
  const isDev = process.env.NODE_ENV === 'development'
  return isDev ? API_CONFIG.dev : API_CONFIG.prod
}

// 获取完整的 API 基础 URL
export const getApiUrl = () => {
  const config = getConfig()
  return `${config.protocol}://${config.host}:${config.port}${config.apiPath}`
}

// WebSocket 配置
export const WS_CONFIG = {
  reconnectInterval: 3000,  // 重连间隔（毫秒）
  maxRetries: 5,             // 最大重试次数
  heartbeatInterval: 30000   // 心跳间隔（毫秒）
}

// 页面标题映射
export const PAGE_TITLES = {
  '/': 'YLAI-AUTO-PLATFORM',
  '/run': '运行任务中心',
  '/monitor': '监控面板',
  '/api-doc': 'API 文档',
  '/api-map': '接口映射',
  '/visual-pipeline': 'DAG 可视化流水线',
  '/rbac': '权限管理',
  '/settings': '系统设置',
  '/about': '关于系统',
  '/history': '历史记录',
  '/stats': '统计分析',
  '/user': '用户管理',
  '/login': '系统登录'
}

// 权限角色定义
export const ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  USER: 'user',
  GUEST: 'guest'
}

// 权限定义
export const PERMISSIONS = {
  // 脚本权限
  VIEW_SCRIPTS: 'scripts:view',
  CREATE_SCRIPTS: 'scripts:create',
  EDIT_SCRIPTS: 'scripts:edit',
  DELETE_SCRIPTS: 'scripts:delete',
  RUN_SCRIPTS: 'scripts:run',
  
  // 任务权限
  VIEW_TASKS: 'tasks:view',
  CREATE_TASKS: 'tasks:create',
  EDIT_TASKS: 'tasks:edit',
  DELETE_TASKS: 'tasks:delete',
  
  // DAG 流水线权限
  VIEW_PIPELINES: 'pipelines:view',
  CREATE_PIPELINES: 'pipelines:create',
  EDIT_PIPELINES: 'pipelines:edit',
  DELETE_PIPELINES: 'pipelines:delete',
  RUN_PIPELINES: 'pipelines:run',
  
  // 系统管理权限
  VIEW_LOGS: 'logs:view',
  VIEW_METRICS: 'metrics:view',
  MANAGE_USERS: 'users:manage',
  MANAGE_ROLES: 'roles:manage',
  MANAGE_SETTINGS: 'settings:manage'
}

// API 端点定义
export const API_ENDPOINTS = {
  // 系统
  HEALTH: '/health',
  SYSTEM_INFO: '/system/info',
  
  // 脚本
  SCRIPTS: '/scripts',
  SCRIPT_RUN: '/scripts/:id/run',
  
  // 任务
  TASKS: '/tasks',
  TASK_DETAIL: '/tasks/:id',
  
  // DAG 流水线
  PIPELINES: '/pipelines',
  PIPELINE_DETAIL: '/pipelines/:id',
  PIPELINE_RUN: '/pipelines/:id/run',
  
  // 监控
  METRICS: '/metrics',
  LOGS: '/logs',
  
  // 用户和权限
  USERS: '/users',
  ROLES: '/roles',
  PERMISSIONS: '/permissions',
  
  // 系统设置
  SETTINGS: '/settings'
}

// HTTP 状态码映射
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503
}

// 错误消息映射
export const ERROR_MESSAGES = {
  [HTTP_STATUS.BAD_REQUEST]: '请求参数错误',
  [HTTP_STATUS.UNAUTHORIZED]: '请先登录',
  [HTTP_STATUS.FORBIDDEN]: '权限不足，无法执行此操作',
  [HTTP_STATUS.NOT_FOUND]: '请求的资源不存在',
  [HTTP_STATUS.CONFLICT]: '资源冲突',
  [HTTP_STATUS.SERVER_ERROR]: '服务器内部错误',
  [HTTP_STATUS.SERVICE_UNAVAILABLE]: '服务暂时不可用，请稍后再试'
}

export default {
  API_CONFIG,
  API_ENDPOINTS,
  ROLES,
  PERMISSIONS,
  HTTP_STATUS,
  ERROR_MESSAGES,
  WS_CONFIG,
  PAGE_TITLES,
  getConfig,
  getApiUrl
}
