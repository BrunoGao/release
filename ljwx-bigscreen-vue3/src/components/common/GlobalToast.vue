<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast" tag="div">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="[
            `toast-${toast.type}`,
            { 'toast-dismissible': toast.dismissible }
          ]"
          @click="toast.dismissible && removeToast(toast.id)"
        >
          <!-- 图标 -->
          <div class="toast-icon">
            <component :is="getIcon(toast.type)" />
          </div>
          
          <!-- 内容 -->
          <div class="toast-content">
            <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
            <div class="toast-message">{{ toast.message }}</div>
          </div>
          
          <!-- 关闭按钮 -->
          <button
            v-if="toast.dismissible"
            class="toast-close"
            @click.stop="removeToast(toast.id)"
          >
            <Close />
          </button>
          
          <!-- 进度条 -->
          <div
            v-if="toast.duration > 0"
            class="toast-progress"
            :style="{ 
              animationDuration: `${toast.duration}ms`,
              animationPlayState: toast.paused ? 'paused' : 'running'
            }"
          />
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { 
  SuccessFilled, 
  WarningFilled, 
  CircleCloseFilled, 
  InfoFilled,
  Close 
} from '@element-plus/icons-vue'

interface Toast {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title?: string
  message: string
  duration: number
  dismissible: boolean
  paused: boolean
  createdAt: number
}

// 状态管理
const toasts = ref<Toast[]>([])
const timers = new Map<string, number>()

// 图标映射
const iconMap = {
  success: SuccessFilled,
  warning: WarningFilled,
  error: CircleCloseFilled,
  info: InfoFilled
}

const getIcon = (type: Toast['type']) => iconMap[type]

// 添加 Toast
const addToast = (options: Partial<Toast> & { message: string }) => {
  const toast: Toast = {
    id: generateId(),
    type: 'info',
    duration: 3000,
    dismissible: true,
    paused: false,
    createdAt: Date.now(),
    ...options
  }
  
  // 限制最大显示数量
  if (toasts.value.length >= 5) {
    removeToast(toasts.value[0].id)
  }
  
  toasts.value.push(toast)
  
  // 自动移除
  if (toast.duration > 0) {
    const timer = window.setTimeout(() => {
      removeToast(toast.id)
    }, toast.duration)
    
    timers.set(toast.id, timer)
  }
  
  return toast.id
}

// 移除 Toast
const removeToast = (id: string) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
    
    // 清理定时器
    const timer = timers.get(id)
    if (timer) {
      clearTimeout(timer)
      timers.delete(id)
    }
  }
}

// 暂停/恢复 Toast
const pauseToast = (id: string) => {
  const toast = toasts.value.find(t => t.id === id)
  if (toast) {
    toast.paused = true
    
    // 暂停定时器
    const timer = timers.get(id)
    if (timer) {
      clearTimeout(timer)
      timers.delete(id)
    }
  }
}

const resumeToast = (id: string) => {
  const toast = toasts.value.find(t => t.id === id)
  if (toast && toast.duration > 0) {
    toast.paused = false
    
    // 计算剩余时间
    const elapsed = Date.now() - toast.createdAt
    const remaining = Math.max(0, toast.duration - elapsed)
    
    if (remaining > 0) {
      const timer = window.setTimeout(() => {
        removeToast(id)
      }, remaining)
      
      timers.set(id, timer)
    } else {
      removeToast(id)
    }
  }
}

// 清空所有 Toast
const clearAll = () => {
  // 清理所有定时器
  timers.forEach(timer => clearTimeout(timer))
  timers.clear()
  
  // 清空列表
  toasts.value = []
}

// 生成唯一ID
const generateId = () => {
  return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 快捷方法
const success = (message: string, options?: Partial<Toast>) => {
  return addToast({ ...options, message, type: 'success' })
}

const warning = (message: string, options?: Partial<Toast>) => {
  return addToast({ ...options, message, type: 'warning' })
}

const error = (message: string, options?: Partial<Toast>) => {
  return addToast({ ...options, message, type: 'error', duration: 5000 })
}

const info = (message: string, options?: Partial<Toast>) => {
  return addToast({ ...options, message, type: 'info' })
}

// 鼠标悬停事件
const handleMouseEnter = (toast: Toast) => {
  pauseToast(toast.id)
}

const handleMouseLeave = (toast: Toast) => {
  resumeToast(toast.id)
}

// 暴露方法给全局使用
defineExpose({
  addToast,
  removeToast,
  clearAll,
  success,
  warning,
  error,
  info
})

// 清理定时器
onUnmounted(() => {
  clearAll()
})

// 全局键盘事件
onMounted(() => {
  const handleKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && toasts.value.length > 0) {
      // Esc 键关闭最新的 Toast
      const latestToast = toasts.value[toasts.value.length - 1]
      if (latestToast.dismissible) {
        removeToast(latestToast.id)
      }
    }
  }
  
  document.addEventListener('keydown', handleKeydown)
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })
})
</script>

<style lang="scss" scoped>
.toast-container {
  position: fixed;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  z-index: var(--z-toast);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  min-width: 320px;
  max-width: 480px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-tertiary);
  position: relative;
  overflow: hidden;
  pointer-events: all;
  cursor: default;
  
  &.toast-dismissible {
    cursor: pointer;
  }
  
  // 类型样式
  &.toast-success {
    border-left: 4px solid var(--success);
    .toast-icon {
      color: var(--success);
    }
  }
  
  &.toast-warning {
    border-left: 4px solid var(--warning);
    .toast-icon {
      color: var(--warning);
    }
  }
  
  &.toast-error {
    border-left: 4px solid var(--error);
    .toast-icon {
      color: var(--error);
    }
  }
  
  &.toast-info {
    border-left: 4px solid var(--info);
    .toast-icon {
      color: var(--info);
    }
  }
  
  // 悬停效果
  &:hover {
    transform: translateX(-4px);
    box-shadow: var(--shadow-xl);
    
    .toast-close {
      opacity: 1;
    }
  }
}

.toast-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
  transition: all var(--duration-fast);
}

.toast-content {
  flex: 1;
  min-width: 0;
  
  .toast-title {
    font-size: var(--font-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
    line-height: var(--leading-tight);
  }
  
  .toast-message {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    line-height: var(--leading-normal);
    word-wrap: break-word;
  }
}

.toast-close {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: all var(--duration-fast);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  width: 100%;
  background: currentColor;
  opacity: 0.3;
  transform-origin: left;
  animation: toastProgress linear forwards;
}

// 过渡动画
.toast-enter-active {
  transition: all var(--duration-normal) var(--ease-out);
}

.toast-leave-active {
  transition: all var(--duration-normal) var(--ease-in);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform var(--duration-normal) var(--ease-out);
}

// 进度条动画
@keyframes toastProgress {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}

// 响应式设计
@media (max-width: 640px) {
  .toast-container {
    top: var(--spacing-sm);
    right: var(--spacing-sm);
    left: var(--spacing-sm);
  }
  
  .toast-item {
    min-width: auto;
    max-width: none;
  }
}

// 可访问性
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active,
  .toast-move {
    transition: none;
  }
  
  .toast-item:hover {
    transform: none;
  }
}

// 高对比度模式
@media (prefers-contrast: high) {
  .toast-item {
    border-width: 2px;
    box-shadow: var(--shadow-xl);
  }
}
</style>