import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 样式导入
import 'element-plus/dist/index.css'
import 'virtual:windi.css'
import '@/assets/styles/global.scss'
import '@/assets/styles/tech-theme.scss'

// 插件导入
import i18n from '@/plugins/i18n'

async function bootstrap() {
  const app = createApp(App)
  
  // 状态管理
  app.use(createPinia())
  
  // 路由
  app.use(router)
  
  // Element Plus
  app.use(ElementPlus)
  
  // Element Plus 图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
  
  // 国际化
  app.use(i18n)
  
  // 全局错误处理
  app.config.errorHandler = (err, vm, info) => {
    console.error('Global error:', err, info)
    // 这里可以集成错误上报服务
  }
  
  // 性能监控
  app.config.performance = true
  
  // 挂载应用
  app.mount('#app')
  
  // 确保系统加载状态被清除
  setTimeout(async () => {
    const { useSystemStore } = await import('@/stores/system')
    const systemStore = useSystemStore()
    systemStore.setLoading(false)
    console.log('🚀 LJWX BigScreen Vue3 启动成功!')
  }, 500)
  
  // 移除初始加载屏幕
  const loadingElement = document.getElementById('initial-loading')
  if (loadingElement) {
    loadingElement.style.opacity = '0'
    setTimeout(() => {
      loadingElement.remove()
    }, 300)
  }
}

bootstrap().catch(err => {
  console.error('应用启动失败:', err)
})