import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'
import history from 'connect-history-api-fallback'

export default defineConfig({
  appType: 'spa',
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // <== 365 days
              },
              cacheKeyWillBeUsed: async ({ request }) => `${request.url}`
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // <== 365 days
              },
              cacheKeyWillBeUsed: async ({ request }) => `${request.url}`
            }
          }
        ]
      },
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'YLAI Auto Platform',
        short_name: 'YLAI',
        description: '企业级AI增强自动化爬虫平台',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  // publicDir: 'static',
  server: {
    host: true, // 自动监听所有网卡，支持 0.0.0.0/localhost/容器
    port: 3001,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 1000,  // 更快的文件监控
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**']
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
        ws: true
      },
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true
      }
    },
    hmr: {
      overlay: true  // 显示错误覆盖层
    },
    fs: {
      strict: false  // 允许访问项目外的文件
    },
    configureServer: (server) => {
      // 添加 history API 回退中间件
      server.middlewares.use(history({
        verbose: false,
        disableDotRule: true,
        rewrites: [
          { from: /^\/$/, to: '/index.html' },
          { from: /^\/(?!.*\.)/, to: '/index.html' }
        ]
      }))
    },
    middlewareMode: false,
    open: '/', // 启动自动打开首页
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '~': path.resolve(__dirname)
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['axios', 'vue-i18n']
        }
      }
    }
  }
})
