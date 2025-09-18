<template>
  <div id="app" class="app-container">
    <!-- 全局背景效果 -->
    <TechBackground />
    
    <!-- 路由视图 -->
    <RouterView v-slot="{ Component, route }">
      <Transition
        :name="route.meta.transition || 'fade'"
        mode="out-in"
        appear
      >
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
    
    <!-- 全局组件 -->
    <GlobalLoading />
    <GlobalToast />
    <GlobalModal />
    
    <!-- 性能监控 -->
    <PerformanceMonitor v-if="isDev" />
  </div>
</template>

<script setup lang="ts">
import { provide, watch, onMounted } from 'vue'
import { useDocumentVisibility, useNetwork } from '@vueuse/core'
import { useSystemStore } from '@/stores/system'
import TechBackground from '@/components/effects/TechBackground.vue'
import GlobalLoading from '@/components/common/GlobalLoading.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import GlobalModal from '@/components/common/GlobalModal.vue'
import PerformanceMonitor from '@/components/common/PerformanceMonitor.vue'

// 系统状态
const systemStore = useSystemStore()

// 开发环境标识
const isDev = import.meta.env.DEV

// 提供全局状态
provide('systemStore', systemStore)

// 监听系统主题变化
watch(
  () => systemStore.theme,
  (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme)
    document.documentElement.className = `theme-${newTheme}`
  },
  { immediate: true }
)

// 页面可见性检测
useDocumentVisibility({
  onHidden() {
    systemStore.setPageVisibility(false)
  },
  onVisible() {
    systemStore.setPageVisibility(true)
  }
})

// 网络状态监控
const { isOnline } = useNetwork()
watch(isOnline, (online) => {
  systemStore.setNetworkStatus(online)
})

// 初始化系统store
systemStore.initializeStore()

// 页面性能监控
onMounted(() => {
  // 监控首屏加载时间
  if (window.performance) {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    const loadTime = navigation.loadEventEnd - navigation.fetchStart
    
    console.log(`📊 页面加载时间: ${Math.round(loadTime)}ms`)
    systemStore.setPerformanceMetric('pageLoadTime', loadTime)
  }
  
  // 确保初始加载状态正确设置
  setTimeout(() => {
    systemStore.setLoading(false)
  }, 1000)
})
</script>

<style lang="scss">
.app-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, 
    var(--bg-primary) 0%, 
    var(--bg-secondary) 100%
  );
}

// 路由过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease-out;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

// 滑动过渡
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

// 缩放过渡
.scale-enter-active,
.scale-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.scale-enter-from {
  transform: scale(0.9);
  opacity: 0;
}

.scale-leave-to {
  transform: scale(1.1);
  opacity: 0;
}
</style>