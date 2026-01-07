import { createI18n } from 'vue-i18n'

const messages = {
  zh: {
    nav: {
      home: '首页',
      run: '运行任务',
      monitor: '监控面板',
      apiDoc: 'API文档',
      visualPipeline: '可视化编排',
      rbac: '权限管理',
      settings: '设置',
      about: '关于',
      aiDemo: 'AI代理',
      apiMap: '接口映射'
    },
    common: {
      loading: '加载中...',
      error: '错误',
      success: '成功',
      cancel: '取消',
      confirm: '确认',
      save: '保存',
      delete: '删除',
      edit: '编辑',
      add: '添加',
      search: '搜索',
      filter: '筛选',
      sort: '排序',
      export: '导出',
      import: '导入'
    },
    index: {
      title: 'YLAI-AUTO-PLATFORM 统一入口',
      functions: '功能列表',
      available: '可用',
      unavailable: '不可用',
      script: '脚本',
      dag: 'DAG'
    },
    run: {
      title: '运行任务中心',
      createTask: '创建新任务',
      script: '脚本',
      params: '参数',
      run: '运行任务',
      running: '运行中...',
      result: '执行结果',
      copyResult: '复制结果'
    },
    monitor: {
      title: '监控面板',
      systemStatus: '系统状态',
      apiCalls: 'API调用',
      memoryUsage: '内存使用',
      cpuUsage: 'CPU使用',
      recentLogs: '最近日志',
      pipelineStatus: '流水线状态',
      healthy: '健康',
      unhealthy: '不健康'
    }
  },
  en: {
    nav: {
      home: 'Home',
      run: 'Run Tasks',
      monitor: 'Monitor',
      apiDoc: 'API Docs',
      visualPipeline: 'Visual Pipeline',
      rbac: 'RBAC',
      aiDemo: 'AI Agent',
      apiMap: 'API Map'
    },
    common: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      cancel: 'Cancel',
      confirm: 'Confirm',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      search: 'Search',
      filter: 'Filter',
      sort: 'Sort',
      export: 'Export',
      import: 'Import'
    },
    index: {
      title: 'YLAI-AUTO-PLATFORM Unified Entry',
      functions: 'Functions',
      available: 'Available',
      unavailable: 'Unavailable',
      script: 'Script',
      dag: 'DAG'
    },
    run: {
      title: 'Task Runner',
      createTask: 'Create New Task',
      script: 'Script',
      params: 'Parameters',
      run: 'Run Task',
      running: 'Running...',
      result: 'Result',
      copyResult: 'Copy Result'
    },
    monitor: {
      title: 'Monitor Dashboard',
      systemStatus: 'System Status',
      apiCalls: 'API Calls',
      memoryUsage: 'Memory Usage',
      cpuUsage: 'CPU Usage',
      recentLogs: 'Recent Logs',
      pipelineStatus: 'Pipeline Status',
      healthy: 'Healthy',
      unhealthy: 'Unhealthy'
    }
  }
}

const i18n = createI18n({
  locale: 'zh', // 默认语言
  fallbackLocale: 'en',
  messages
})

export default i18n