<template>
  <div class="view-layout">
    <div class="view-header">
      <div class="header-left">
        <el-button @click="goBack" size="small" type="primary">
          <el-icon><ArrowLeft /></el-icon>
          返回大屏
        </el-button>
      </div>
      <div class="header-center">
        <h2 class="view-title">{{ viewTitle }}</h2>
      </div>
      <div class="header-right">
        <el-button @click="toggleFullscreen" size="small">
          <el-icon><FullScreen /></el-icon>
          全屏
        </el-button>
      </div>
    </div>
    
    <div class="view-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, FullScreen } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()

const viewTitle = computed(() => {
  const titleMap: Record<string, string> = {
    alert: '告警管理中心',
    message: '消息管理中心',
    health: '健康数据中心',
    device: '设备监控中心',
    track: '轨迹跟踪中心',
    user: '用户管理中心'
  }
  const pathSegments = route.path.split('/')
  const viewType = pathSegments[pathSegments.length - 1]
  return titleMap[viewType] || '数据中心'
})

const goBack = () => {
  router.push('/')
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}
</script>

<style lang="scss" scoped>
.view-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  height: 60px;
  flex-shrink: 0;
  
  .header-left,
  .header-right {
    flex: 0 0 120px;
  }
  
  .header-center {
    flex: 1;
    text-align: center;
    
    .view-title {
      margin: 0;
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

.view-content {
  flex: 1;
  overflow: hidden;
  padding: var(--spacing-md);
}

@media (max-width: 768px) {
  .view-header {
    padding: var(--spacing-sm) var(--spacing-md);
    
    .header-left,
    .header-right {
      flex: 0 0 auto;
    }
  }
  
  .view-content {
    padding: var(--spacing-sm);
  }
}
</style>