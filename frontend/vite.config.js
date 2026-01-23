import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

// 检测是否为 GitHub Pages 构建
const isGitHubPages = process.env.BUILD_TARGET === 'github'

// GitHub Pages 构建后处理插件
const githubPagesPlugin = () => ({
  name: 'github-pages',
  closeBundle() {
    if (isGitHubPages) {
      const docsDir = path.resolve(__dirname, '../docs')
      // 创建 .nojekyll 禁用 Jekyll
      fs.writeFileSync(path.join(docsDir, '.nojekyll'), '')
      // 复制 index.html 为 404.html 处理 SPA 路由
      const indexPath = path.join(docsDir, 'index.html')
      const notFoundPath = path.join(docsDir, '404.html')
      if (fs.existsSync(indexPath)) {
        fs.copyFileSync(indexPath, notFoundPath)
      }
      console.log('Created .nojekyll and 404.html')
    }
  }
})

export default defineConfig({
  plugins: [vue(), githubPagesPlugin()],
  // GitHub Pages 需要设置 base 路径（仓库名）
  base: isGitHubPages ? '/ugv_web/' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3080,
    proxy: {
      '/api': {
        target: 'http://localhost:5080',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'http://localhost:5080',
        changeOrigin: true,
        ws: true
      },
      '/video_feed': {
        target: 'http://localhost:5080',
        changeOrigin: true
      }
    }
  },
  build: {
    // GitHub Pages 输出到根目录的 docs，正常构建输出到 backend/static
    outDir: isGitHubPages ? '../docs' : '../backend/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'echarts': ['echarts', 'vue-echarts']
        }
      }
    }
  },
  define: {
    // GitHub Pages 构建时自动启用 mock 模式
    'import.meta.env.VITE_MOCK': JSON.stringify(isGitHubPages ? 'true' : 'false')
  }
})
