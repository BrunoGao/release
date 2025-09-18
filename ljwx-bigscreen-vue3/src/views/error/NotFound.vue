<template>
  <div class="not-found">
    <div class="error-container">
      <div class="error-icon">
        <el-icon><Warning /></el-icon>
      </div>
      <h1 class="error-title">404</h1>
      <p class="error-message">抱歉，您访问的页面不存在</p>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Warning, HomeFilled, ArrowLeft } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.not-found {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.error-container {
  text-align: center;
  max-width: 400px;
  padding: var(--spacing-xl);
  
  .error-icon {
    font-size: 80px;
    color: var(--warning-500);
    margin-bottom: var(--spacing-lg);
  }
  
  .error-title {
    font-size: 72px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
    font-family: var(--font-tech);
  }
  
  .error-message {
    font-size: var(--font-lg);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xl);
  }
  
  .error-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .error-container {
    padding: var(--spacing-lg);
    
    .error-title {
      font-size: 48px;
    }
    
    .error-actions {
      flex-direction: column;
      align-items: center;
    }
  }
}
</style>