<template>
  <Teleport to="body">
    <Transition name="loading">
      <div v-if="isVisible" class="global-loading">
        <div class="loading-backdrop" />
        
        <div class="loading-content">
          <!-- 主加载动画 -->
          <div class="loading-spinner">
            <div class="spinner-ring">
              <div class="ring-segment" v-for="i in 8" :key="i" />
            </div>
            <div class="spinner-core">
              <div class="core-pulse" />
            </div>
          </div>
          
          <!-- 加载文本 -->
          <div class="loading-text">
            <div class="text-main">{{ currentText }}</div>
            <div class="text-sub">{{ progressText }}</div>
          </div>
          
          <!-- 进度条 -->
          <div v-if="showProgress" class="loading-progress">
            <div class="progress-track">
              <div 
                class="progress-fill" 
                :style="{ width: `${progress}%` }"
              />
              <div class="progress-glow" />
            </div>
            <div class="progress-text">{{ progress }}%</div>
          </div>
          
          <!-- 加载步骤 -->
          <div v-if="steps.length > 0" class="loading-steps">
            <div 
              v-for="(step, index) in steps" 
              :key="index"
              class="step-item"
              :class="{
                'step-completed': index < currentStep,
                'step-active': index === currentStep,
                'step-pending': index > currentStep
              }"
            >
              <div class="step-icon">
                <Check v-if="index < currentStep" class="icon-check" />
                <Loading v-else-if="index === currentStep" class="icon-loading" />
                <More v-else class="icon-pending" />
              </div>
              <div class="step-text">{{ step }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { Check, Loading, More } from '@element-plus/icons-vue'
import { useSystemStore } from '@/stores/system'

interface LoadingStep {
  text: string
  duration?: number
}

// 系统状态
const systemStore = useSystemStore()

// 组件状态
const isVisible = computed(() => systemStore.isLoading)
const currentText = computed(() => systemStore.loadingText)

// 进度相关
const progress = ref(0)
const showProgress = ref(false)
const progressText = computed(() => {
  if (progress.value === 100) return '完成'
  if (progress.value === 0) return '准备中'
  return `${progress.value}%`
})

// 步骤相关
const steps = ref<string[]>([])
const currentStep = ref(0)

// 动态文本切换
const textVariations = [
  '正在加载数据...',
  '正在渲染界面...',
  '正在建立连接...',
  '正在优化性能...'
]
const textIndex = ref(0)

// 文本轮换
const rotateText = () => {
  if (!isVisible.value) return
  
  textIndex.value = (textIndex.value + 1) % textVariations.length
  setTimeout(rotateText, 2000)
}

// 模拟进度更新
const updateProgress = () => {
  if (!isVisible.value || !showProgress.value) return
  
  const increment = Math.random() * 10 + 5
  progress.value = Math.min(100, progress.value + increment)
  
  if (progress.value < 100) {
    setTimeout(updateProgress, 200 + Math.random() * 300)
  }
}

// 监听加载状态变化
watch(isVisible, (visible) => {
  if (visible) {
    progress.value = 0
    currentStep.value = 0
    textIndex.value = 0
    
    // 开始文本轮换
    setTimeout(rotateText, 1000)
    
    // 如果有进度需求，开始进度更新
    if (showProgress.value) {
      setTimeout(updateProgress, 500)
    }
  }
})

// 设置加载步骤
const setSteps = (stepList: string[]) => {
  steps.value = stepList
  currentStep.value = 0
}

// 更新当前步骤
const nextStep = () => {
  if (currentStep.value < steps.value.length - 1) {
    currentStep.value++
  }
}

// 设置进度
const setProgress = (value: number, show = true) => {
  progress.value = Math.max(0, Math.min(100, value))
  showProgress.value = show
}

// 暴露方法给外部使用
defineExpose({
  setSteps,
  nextStep,
  setProgress
})

// 性能优化：减少不必要的重渲染
const shouldRender = computed(() => isVisible.value)
</script>

<style lang="scss" scoped>
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: var(--z-loading);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
}

.loading-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xl);
  padding: var(--spacing-2xl);
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  backdrop-filter: blur(10px);
  min-width: 300px;
}

// ========== 加载动画 ==========

.loading-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  
  .ring-segment {
    position: absolute;
    width: 8px;
    height: 8px;
    background: var(--primary-500);
    border-radius: 50%;
    box-shadow: var(--shadow-glow);
    
    @for $i from 1 through 8 {
      &:nth-child(#{$i}) {
        top: 50%;
        left: 50%;
        transform: 
          translate(-50%, -50%) 
          rotate(#{($i - 1) * 45}deg) 
          translateY(-30px);
        animation: spinnerPulse 1.5s ease-in-out infinite;
        animation-delay: #{($i - 1) * 0.15}s;
      }
    }
  }
}

.spinner-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  
  .core-pulse {
    width: 100%;
    height: 100%;
    background: var(--tech-500);
    border-radius: 50%;
    animation: corePulse 1s ease-in-out infinite alternate;
  }
}

// ========== 文本区域 ==========

.loading-text {
  text-align: center;
  
  .text-main {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
    animation: textGlow 2s ease-in-out infinite alternate;
  }
  
  .text-sub {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    font-family: var(--font-mono);
  }
}

// ========== 进度条 ==========

.loading-progress {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  
  .progress-track {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-full);
    position: relative;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary-500), var(--tech-500));
      border-radius: var(--radius-full);
      transition: width 0.3s ease-out;
      position: relative;
    }
    
    .progress-glow {
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      width: 30px;
      background: linear-gradient(90deg, 
        transparent, 
        rgba(255, 255, 255, 0.5), 
        transparent
      );
      animation: progressScan 2s linear infinite;
    }
  }
  
  .progress-text {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    font-family: var(--font-mono);
    min-width: 40px;
    text-align: right;
  }
}

// ========== 步骤列表 ==========

.loading-steps {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  
  .step-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm);
    border-radius: var(--radius-md);
    transition: all var(--duration-normal);
    
    &.step-completed {
      .step-icon {
        background: var(--success);
        color: white;
      }
      .step-text {
        color: var(--text-secondary);
        text-decoration: line-through;
      }
    }
    
    &.step-active {
      background: rgba(0, 255, 157, 0.1);
      border: 1px solid var(--primary-500);
      
      .step-icon {
        background: var(--primary-500);
        color: white;
        animation: iconSpin 1s linear infinite;
      }
      .step-text {
        color: var(--primary-500);
        font-weight: 600;
      }
    }
    
    &.step-pending {
      .step-icon {
        background: rgba(255, 255, 255, 0.1);
        color: var(--text-tertiary);
      }
      .step-text {
        color: var(--text-tertiary);
      }
    }
  }
  
  .step-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    transition: all var(--duration-normal);
  }
  
  .step-text {
    font-size: var(--font-sm);
    transition: all var(--duration-normal);
  }
}

// ========== 动画定义 ==========

@keyframes spinnerPulse {
  0%, 100% {
    opacity: 0.3;
    transform: 
      translate(-50%, -50%) 
      rotate(var(--rotation)) 
      translateY(-30px) 
      scale(0.8);
  }
  50% {
    opacity: 1;
    transform: 
      translate(-50%, -50%) 
      rotate(var(--rotation)) 
      translateY(-30px) 
      scale(1.2);
  }
}

@keyframes corePulse {
  0% {
    opacity: 0.6;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@keyframes progressScan {
  0% {
    left: -30px;
  }
  100% {
    left: 100%;
  }
}

@keyframes iconSpin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// ========== 过渡动画 ==========

.loading-enter-active,
.loading-leave-active {
  transition: all var(--duration-slow) var(--ease-out);
}

.loading-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.loading-leave-to {
  opacity: 0;
  transform: scale(1.1);
}

// ========== 响应式设计 ==========

@media (max-width: 640px) {
  .loading-content {
    margin: var(--spacing-md);
    padding: var(--spacing-lg);
    min-width: auto;
    width: calc(100% - 2 * var(--spacing-md));
  }
  
  .loading-spinner {
    width: 60px;
    height: 60px;
  }
  
  .loading-steps .step-item {
    padding: var(--spacing-xs);
    gap: var(--spacing-sm);
  }
}

// ========== 可访问性 ==========

@media (prefers-reduced-motion: reduce) {
  .spinner-ring,
  .core-pulse,
  .progress-glow {
    animation: none;
  }
  
  .step-active .step-icon {
    animation: none;
  }
}
</style>