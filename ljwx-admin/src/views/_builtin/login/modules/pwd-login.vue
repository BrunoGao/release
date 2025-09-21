<script setup lang="ts">
import { computed, reactive } from 'vue';
import { NSelect } from 'naive-ui';
import { $t } from '@/locales';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { useAuthStore } from '@/store/modules/auth';
import { sha256 } from '@/utils/crypto';

defineOptions({
  name: 'PwdLogin'
});

const authStore = useAuthStore();
const { formRef, validate } = useNaiveForm();

interface FormModel {
  userName: string;
  password: string;
  orgId: string;
}

const model: FormModel = reactive({
  userName: 'admin',
  password: 'kt123456',
  orgId: '1'
});

const rules = computed<Record<keyof FormModel, App.Global.FormRule[]>>(() => {
  // inside computed to make locale reactive, if not apply i18n, you can define it without computed
  const { formRules } = useFormRules();

  return {
    userName: formRules.userName,
    password: formRules.pwd,
    orgId: formRules.orgId
  };
});

async function handleSubmit() {
  await validate();
  await authStore.login(model.userName, sha256(model.password));
}
</script>

<template>
  <div class="health-login-form">
    <NForm ref="formRef" :model="model" :rules="rules" size="large" :show-label="false" @keyup.enter="handleSubmit">
      <!-- 用户名输入框 -->
      <NFormItem path="userName" class="form-item">
        <div class="input-container">
          <div class="input-icon">
            <svg viewBox="0 0 24 24" class="icon-svg">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <NInput 
            v-model:value="model.userName" 
            size="large" 
            class="health-input"
            :placeholder="$t('page.login.common.userNamePlaceholder')" 
          />
        </div>
      </NFormItem>
      
      <!-- 密码输入框 -->
      <NFormItem path="password" class="form-item">
        <div class="input-container">
          <div class="input-icon">
            <svg viewBox="0 0 24 24" class="icon-svg">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM12 17c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM15.1 8H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
            </svg>
          </div>
          <NInput
            v-model:value="model.password"
            size="large"
            type="password"
            show-password-on="click"
            class="health-input"
            :placeholder="$t('page.login.common.passwordPlaceholder')"
          />
        </div>
      </NFormItem>
      
      <!-- 科技状态指示器 -->
      <div class="tech-status-panel">
        <div class="status-grid">
          <div class="status-item" v-for="i in 6" :key="i">
            <div class="status-dot" :class="'status-' + ((i % 3) + 1)" :style="{ animationDelay: i * 0.2 + 's' }"></div>
            <div class="status-line"></div>
          </div>
        </div>
        <div class="system-info">
          <div class="info-text">智能健康监测系统 v2.0</div>
          <div class="connection-status">
            <span class="status-indicator online"></span>
            <span>系统在线</span>
          </div>
        </div>
      </div>
      
      <!-- 登录按钮 -->
      <NSpace vertical :size="24" class="button-space">
        <NButton 
          type="primary" 
          size="large" 
          block 
          class="health-login-btn"
          :loading="authStore.loginLoading" 
          @click="handleSubmit"
        >
          <template #icon>
            <div class="btn-icon">
              <svg viewBox="0 0 24 24" class="login-icon">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
              </svg>
            </div>
          </template>
          {{ $t('common.confirm') }}
        </NButton>
      </NSpace>
      
      <!-- 健康数据可视化小图标 -->
      <div class="health-indicators">
        <div class="indicator" v-for="i in 5" :key="i">
          <div class="indicator-bar" :style="{ height: (30 + i * 15) + '%', animationDelay: i * 0.3 + 's' }"></div>
        </div>
      </div>
    </NForm>
  </div>
</template>

<style scoped>
.health-login-form {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.form-item {
  margin-bottom: 24px;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 16px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.input-container:hover {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.25);
}

.input-container:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2);
  background: rgba(15, 23, 42, 0.9);
}

.input-icon {
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(45deg, #3b82f6, #1e40af);
  height: 56px;
  min-width: 56px;
  position: relative;
}

.input-icon::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: iconShine 3s ease-in-out infinite;
}

@keyframes iconShine {
  0%, 100% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
}

.icon-svg {
  width: 24px;
  height: 24px;
  fill: white;
}

:deep(.health-input) {
  flex: 1;
  border: none !important;
  border-radius: 0 16px 16px 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 16px;
  font-weight: 500;
  color: #2d3748;
}

:deep(.health-input input) {
  padding: 16px 20px;
  font-size: 16px;
  color: #e2e8f0;
  background: transparent !important;
}

:deep(.health-input input::placeholder) {
  color: #64748b;
  font-weight: 400;
}

.tech-status-panel {
  margin: 20px 0 30px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(15, 23, 42, 0.95));
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  position: relative;
  overflow: hidden;
}

.tech-status-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
  animation: scanLine 3s ease-in-out infinite;
}

@keyframes scanLine {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.status-grid {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 0 8px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: relative;
  animation: techPulse 2s ease-in-out infinite;
}

.status-1 {
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.status-2 {
  background: #3b82f6;
  box-shadow: 0 0 10px #3b82f6;
}

.status-3 {
  background: #8b5cf6;
  box-shadow: 0 0 10px #8b5cf6;
}

.status-dot::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 50%;
  border: 1px solid currentColor;
  opacity: 0;
  animation: techRipple 2s ease-in-out infinite;
}

@keyframes techPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2);
  }
}

@keyframes techRipple {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(2);
  }
}

.status-line {
  width: 1px;
  height: 20px;
  background: linear-gradient(to bottom, transparent, rgba(59, 130, 246, 0.5), transparent);
}

.system-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
}

.info-text {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  letter-spacing: 0.5px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: statusBlink 2s ease-in-out infinite;
}

.status-indicator.online {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

@keyframes statusBlink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.button-space {
  margin-top: 30px;
}

:deep(.health-login-btn) {
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(45deg, #0f172a 0%, #1e293b 25%, #3b82f6 50%, #1e293b 75%, #0f172a 100%);
  background-size: 300% 100%;
  border: 2px solid #3b82f6;
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4), 0 0 50px rgba(59, 130, 246, 0.2);
  animation: buttonPulse 2s ease-in-out infinite;
}

@keyframes buttonPulse {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

:deep(.health-login-btn:hover) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(59, 130, 246, 0.6), 0 0 70px rgba(59, 130, 246, 0.4);
  border-color: #60a5fa;
}

:deep(.health-login-btn:active) {
  transform: translateY(0);
}

:deep(.health-login-btn::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.4), transparent);
  transition: left 0.6s ease;
}

:deep(.health-login-btn:hover::before) {
  left: 100%;
}

:deep(.health-login-btn::after) {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  background: linear-gradient(45deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9));
  border-radius: 14px;
  z-index: -1;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
}

.login-icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.health-indicators {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 30px;
  padding: 20px;
}

.indicator {
  width: 4px;
  height: 40px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.indicator-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(to top, #3b82f6, #8b5cf6, #10b981);
  border-radius: 2px;
  animation: healthPulse 2s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

@keyframes healthPulse {
  0%, 100% {
    opacity: 0.7;
    transform: scaleY(0.8);
  }
  50% {
    opacity: 1;
    transform: scaleY(1.2);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .health-login-form {
    max-width: 100%;
  }
  
  .input-container {
    border-radius: 12px;
  }
  
  .input-icon {
    height: 50px;
    min-width: 50px;
    padding: 0 14px;
  }
  
  .icon-svg {
    width: 20px;
    height: 20px;
  }
  
  :deep(.health-input) {
    border-radius: 0 12px 12px 0 !important;
  }
  
  :deep(.health-input input) {
    padding: 14px 16px;
    font-size: 15px;
  }
  
  :deep(.health-login-btn) {
    height: 50px;
    border-radius: 12px;
    font-size: 15px;
  }
  
  .tech-status-panel {
    padding: 20px;
    border-radius: 12px;
  }
  
  .system-info {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .form-item {
    margin-bottom: 20px;
  }
  
  .input-container {
    border-radius: 10px;
  }
  
  .input-icon {
    height: 48px;
    min-width: 48px;
    padding: 0 12px;
  }
  
  :deep(.health-input) {
    border-radius: 0 10px 10px 0 !important;
  }
  
  :deep(.health-input input) {
    padding: 12px 14px;
    font-size: 14px;
  }
  
  :deep(.health-login-btn) {
    height: 48px;
    border-radius: 10px;
    font-size: 14px;
  }
  
  .tech-status-panel {
    margin: 16px 0 24px;
    padding: 18px;
  }
  
  .health-indicators {
    margin-top: 24px;
    padding: 16px;
  }
  
  .indicator {
    width: 3px;
    height: 30px;
  }
}
</style>
