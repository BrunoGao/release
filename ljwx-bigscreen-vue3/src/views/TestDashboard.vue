<template>
  <div class="test-dashboard">
    <div class="test-container">
      <h1 class="test-title">🚀 LJWX 健康大屏系统</h1>
      <p class="test-subtitle">系统正常运行中...</p>
      
      <div class="test-stats">
        <div class="stat-item">
          <div class="stat-value">{{ onlineTime }}</div>
          <div class="stat-label">运行时间</div>
        </div>
        
        <div class="stat-item">
          <div class="stat-value">{{ systemStore.theme }}</div>
          <div class="stat-label">当前主题</div>
        </div>
        
        <div class="stat-item">
          <div class="stat-value">{{ systemStore.isOnline ? '在线' : '离线' }}</div>
          <div class="stat-label">网络状态</div>
        </div>
      </div>
      
      <div class="test-actions">
        <el-button type="primary" @click="testFunction">
          <el-icon><Check /></el-icon>
          测试功能
        </el-button>
        
        <el-button @click="switchTheme">
          <el-icon><Setting /></el-icon>
          切换主题
        </el-button>
      </div>
      
      <div class="test-info">
        <p>✅ Vue 3 + TypeScript + Vite 正常运行</p>
        <p>✅ Element Plus 组件库已加载</p>
        <p>✅ Pinia 状态管理正常</p>
        <p>✅ Vue Router 路由正常</p>
        <p>✅ SCSS 样式处理正常</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, Setting } from '@element-plus/icons-vue'
import { useSystemStore } from '@/stores/system'
import { ElMessage } from 'element-plus'

const systemStore = useSystemStore()

// 运行时间计算
const startTime = Date.now()
const onlineTime = ref('0s')

const updateOnlineTime = () => {
  const elapsed = Date.now() - startTime
  const seconds = Math.floor(elapsed / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    onlineTime.value = `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    onlineTime.value = `${minutes}m ${seconds % 60}s`
  } else {
    onlineTime.value = `${seconds}s`
  }
}

// 测试功能
const testFunction = () => {
  ElMessage.success('系统功能测试正常！')
}

// 切换主题
const switchTheme = () => {
  const newTheme = systemStore.theme === 'dark' ? 'light' : 'dark'
  systemStore.setTheme(newTheme)
  ElMessage.info(`已切换到${newTheme === 'dark' ? '深色' : '浅色'}主题`)
}

// 定时更新在线时间
onMounted(() => {
  const timer = setInterval(updateOnlineTime, 1000)
  
  onUnmounted(() => {
    clearInterval(timer)
  })
})
</script>

<style lang="scss" scoped>
.test-dashboard {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, 
    var(--bg-primary) 0%, 
    var(--bg-secondary) 50%,
    var(--bg-tertiary) 100%);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 20% 30%, rgba(0, 255, 157, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(0, 228, 255, 0.1) 0%, transparent 50%);
    pointer-events: none;
  }
}

.test-container {
  text-align: center;
  padding: var(--spacing-2xl);
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-2xl);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  z-index: 1;
}

.test-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
  background: linear-gradient(135deg, var(--primary-500), var(--tech-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(0, 255, 157, 0.3);
}

.test-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2xl);
}

.test-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
  
  .stat-item {
    padding: var(--spacing-lg);
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--primary-500);
      font-family: var(--font-tech);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-label {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.test-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
  margin-bottom: var(--spacing-2xl);
}

.test-info {
  text-align: left;
  background: rgba(0, 0, 0, 0.3);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--success-500);
  
  p {
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: var(--spacing-sm);
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

@media (max-width: 768px) {
  .test-container {
    margin: var(--spacing-md);
    padding: var(--spacing-lg);
  }
  
  .test-title {
    font-size: 32px;
  }
  
  .test-stats {
    grid-template-columns: 1fr;
  }
  
  .test-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>