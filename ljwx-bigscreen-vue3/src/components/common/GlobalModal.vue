<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="global-modal-overlay"
      @click="handleOverlayClick"
    >
      <div
        class="global-modal"
        :class="[
          `modal-${size}`,
          { 'modal-fullscreen': fullscreen }
        ]"
        @click.stop
      >
        <div class="modal-header">
          <div class="modal-title">
            <el-icon v-if="icon" class="title-icon">
              <component :is="icon" />
            </el-icon>
            <h3>{{ title }}</h3>
          </div>
          <div class="modal-actions">
            <el-button
              v-if="showMinimize"
              type="text"
              size="small"
              @click="handleMinimize"
            >
              <el-icon><Minus /></el-icon>
            </el-button>
            <el-button
              v-if="showMaximize"
              type="text"
              size="small"
              @click="handleMaximize"
            >
              <el-icon><FullScreen /></el-icon>
            </el-button>
            <el-button
              type="text"
              size="small"
              @click="handleClose"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="modal-body">
          <slot></slot>
        </div>
        
        <div v-if="showFooter" class="modal-footer">
          <slot name="footer">
            <el-button @click="handleCancel">{{ cancelText }}</el-button>
            <el-button 
              type="primary" 
              @click="handleConfirm"
              :loading="confirmLoading"
            >
              {{ confirmText }}
            </el-button>
          </slot>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { Close, Minus, FullScreen } from '@element-plus/icons-vue'

interface Props {
  visible?: boolean
  title?: string
  icon?: any
  size?: 'small' | 'medium' | 'large'
  fullscreen?: boolean
  showFooter?: boolean
  showMinimize?: boolean
  showMaximize?: boolean
  closeOnClickOutside?: boolean
  confirmText?: string
  cancelText?: string
  confirmLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  title: '弹窗',
  size: 'medium',
  fullscreen: false,
  showFooter: true,
  showMinimize: false,
  showMaximize: true,
  closeOnClickOutside: true,
  confirmText: '确定',
  cancelText: '取消',
  confirmLoading: false
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'confirm': []
  'cancel': []
  'close': []
  'minimize': []
  'maximize': []
}>()

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}

const handleMinimize = () => {
  emit('minimize')
}

const handleMaximize = () => {
  emit('maximize')
}

const handleOverlayClick = () => {
  if (props.closeOnClickOutside) {
    handleClose()
  }
}

// 监听ESC键关闭弹窗
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.visible) {
    handleClose()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style lang="scss" scoped>
.global-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.global-modal {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  animation: slideIn 0.3s ease;
  border: 1px solid var(--border-light);
  
  &.modal-small {
    width: 400px;
    min-height: 200px;
  }
  
  &.modal-medium {
    width: 600px;
    min-height: 300px;
  }
  
  &.modal-large {
    width: 800px;
    min-height: 400px;
  }
  
  &.modal-fullscreen {
    width: 95vw;
    height: 95vh;
    max-height: none;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-elevated);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  
  .modal-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .title-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    h3 {
      margin: 0;
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .modal-actions {
    display: flex;
    gap: var(--spacing-xs);
    
    .el-button {
      padding: 4px;
      border: none;
      background: transparent;
      color: var(--text-secondary);
      
      &:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
      }
      
      .el-icon {
        font-size: 16px;
      }
    }
  }
}

.modal-body {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--border-light);
    border-radius: var(--radius-sm);
    
    &:hover {
      background: var(--border-dark);
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-light);
  background: var(--bg-elevated);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

@media (max-width: 768px) {
  .global-modal {
    width: 95vw !important;
    margin: var(--spacing-md);
    
    &.modal-fullscreen {
      width: 100vw !important;
      height: 100vh !important;
      margin: 0;
      border-radius: 0;
    }
  }
  
  .modal-header {
    padding: var(--spacing-md);
    
    .modal-title h3 {
      font-size: var(--font-md);
    }
  }
  
  .modal-body {
    padding: var(--spacing-md);
  }
  
  .modal-footer {
    padding: var(--spacing-md);
    flex-direction: column;
    
    .el-button {
      width: 100%;
      margin: 0;
    }
  }
}
</style>