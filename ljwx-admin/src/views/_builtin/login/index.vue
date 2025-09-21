<script setup lang="ts">
import { computed } from 'vue';
import type { Component } from 'vue';
import { getPaletteColorByNumber, mixColor } from '@sa/color';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useThemeStore } from '@/store/modules/theme';
import { loginModuleRecord } from '@/constants/app';
import PwdLogin from './modules/pwd-login.vue';
import CodeLogin from './modules/code-login.vue';
import Register from './modules/register.vue';
import ResetPwd from './modules/reset-pwd.vue';
import BindWechat from './modules/bind-wechat.vue';

interface Props {
  /** The login module */
  module?: UnionKey.LoginModule;
}

const props = defineProps<Props>();

const appStore = useAppStore();
const themeStore = useThemeStore();

interface LoginModule {
  label: string;
  component: Component;
}

const moduleMap: Record<UnionKey.LoginModule, LoginModule> = {
  'pwd-login': { label: loginModuleRecord['pwd-login'], component: PwdLogin },
  'code-login': { label: loginModuleRecord['code-login'], component: CodeLogin },
  register: { label: loginModuleRecord.register, component: Register },
  'reset-pwd': { label: loginModuleRecord['reset-pwd'], component: ResetPwd },
  'bind-wechat': { label: loginModuleRecord['bind-wechat'], component: BindWechat }
};

const activeModule = computed(() => moduleMap[props.module || 'pwd-login']);

const bgThemeColor = computed(() => (themeStore.darkMode ? getPaletteColorByNumber(themeStore.themeColor, 600) : themeStore.themeColor));

const bgColor = computed(() => {
  const COLOR_WHITE = '#ffffff';

  const ratio = themeStore.darkMode ? 0.5 : 0.2;

  return mixColor(COLOR_WHITE, themeStore.themeColor, ratio);
});
</script>

<template>
  <div class="health-login-container">
    <!-- 健康监测背景动画 -->
    <div class="health-bg-animation">
      <div class="heartbeat-circle pulse"></div>
      <div class="heartbeat-circle pulse delay-1"></div>
      <div class="heartbeat-circle pulse delay-2"></div>
      
      <!-- 健康数据流动效果 -->
      <div class="data-stream">
        <div class="data-particle" v-for="i in 8" :key="i" :style="{ animationDelay: i * 0.5 + 's' }"></div>
      </div>
      
      <!-- 智能网格背景 -->
      <div class="ai-grid">
        <div class="grid-line" v-for="i in 12" :key="'h' + i" :class="'horizontal-' + i"></div>
        <div class="grid-line" v-for="i in 12" :key="'v' + i" :class="'vertical-' + i"></div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="login-main-content">
      <!-- 左侧健康概念展示 -->
      <div class="health-showcase">
        <div class="health-icon-container">
          <!-- 心率监测图标 -->
          <div class="health-icon heartrate">
            <svg viewBox="0 0 24 24" class="heartrate-svg">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            <div class="pulse-line"></div>
          </div>
          
          <!-- 智能大脑图标 -->
          <div class="health-icon ai-brain">
            <svg viewBox="0 0 24 24" class="brain-svg">
              <path d="M9.5 2C7.01 2 5 4.01 5 6.5c0 .58.12 1.13.32 1.64C4.56 8.65 4 9.53 4 10.5c0 .96.54 1.84 1.32 2.36C5.12 13.37 5 13.92 5 14.5c0 .96.54 1.84 1.32 2.36-.2.51-.32 1.06-.32 1.64C6 21.01 8.01 23 10.5 23c.58 0 1.13-.12 1.64-.32.51.2 1.06.32 1.64.32C16.29 23 18.3 21.01 18.3 18.5c0-.58-.12-1.13-.32-1.64.78-.52 1.32-1.4 1.32-2.36 0-.58-.12-1.13-.32-1.64.78-.52 1.32-1.4 1.32-2.36 0-.97-.56-1.85-1.32-2.36.2-.51.32-1.06.32-1.64C19.3 4.01 17.29 2 14.8 2c-.58 0-1.13.12-1.64.32C12.65 2.12 12.1 2 11.52 2c-.58 0-1.13.12-1.64.32C9.37 2.12 8.82 2 8.24 2H9.5z"/>
            </svg>
            <div class="ai-particles">
              <div class="particle" v-for="i in 6" :key="i"></div>
            </div>
          </div>

          <!-- 健康数据图标 -->
          <div class="health-icon data-chart">
            <svg viewBox="0 0 24 24" class="chart-svg">
              <path d="M3 17l6-6 4 4 8-8V7h-2v4.5L15 15.5l-4-4L5 17H3zm16-10V3h2v4h4v2h-4z"/>
            </svg>
            <div class="chart-bars">
              <div class="bar" v-for="i in 5" :key="i" :style="{ height: (20 + i * 15) + '%', animationDelay: i * 0.2 + 's' }"></div>
            </div>
          </div>
        </div>
        
        <div class="showcase-text">
          <h1 class="health-title">
            <span class="gradient-text">智能健康</span>
            <span class="normal-text">监测系统</span>
          </h1>
          <p class="health-subtitle">基于人工智能的实时健康数据分析与预警平台</p>
          <div class="feature-list">
            <div class="feature-item">
              <div class="feature-icon">💗</div>
              <span>实时心率监测</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">🧠</div>
              <span>AI智能分析</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">📊</div>
              <span>健康数据可视化</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form-section">
        <!-- 系统控制区域 -->
        <div class="system-controls">
          <div class="logo-title-section">
            <SystemLogo class="system-logo" />
            <h2 class="system-title">{{ $t('system.title') }}</h2>
          </div>
          <div class="control-buttons">
            <ThemeSchemaSwitch
              :theme-schema="themeStore.themeScheme"
              :show-tooltip="false"
              class="control-btn"
              @switch="themeStore.toggleThemeScheme"
            />
            <LangSwitch 
              :lang="appStore.locale" 
              :lang-options="appStore.localeOptions" 
              :show-tooltip="false" 
              class="control-btn"
              @change-lang="appStore.changeLocale" 
            />
          </div>
        </div>

        <!-- 登录卡片 -->
        <div class="login-card">
          <div class="card-header">
            <h3 class="login-title">{{ $t(activeModule.label) }}</h3>
            <div class="title-decoration"></div>
          </div>
          
          <div class="card-content">
            <Transition :name="themeStore.page.animateMode" mode="out-in" appear>
              <component :is="activeModule.component" />
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 全局容器样式 */
.health-login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.health-login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 30% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 40% 90%, rgba(16, 185, 129, 0.15) 0%, transparent 50%);
  z-index: 1;
  pointer-events: none;
}

.health-login-container::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(59, 130, 246, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: 1;
  pointer-events: none;
  animation: gridShift 20s linear infinite;
}

@keyframes gridShift {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(50px, 50px);
  }
}

/* 健康监测背景动画 */
.health-bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

/* 心跳圆圈动画 */
.heartbeat-circle {
  position: absolute;
  width: 100px;
  height: 100px;
  border: 2px solid rgba(59, 130, 246, 0.4);
  border-radius: 50%;
  animation: heartbeat 2s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3), inset 0 0 20px rgba(59, 130, 246, 0.1);
}

.heartbeat-circle:nth-child(1) {
  top: 20%;
  left: 10%;
  width: 80px;
  height: 80px;
}

.heartbeat-circle:nth-child(2) {
  top: 60%;
  right: 15%;
  width: 120px;
  height: 120px;
}

.heartbeat-circle:nth-child(3) {
  bottom: 20%;
  left: 20%;
  width: 60px;
  height: 60px;
}

.delay-1 {
  animation-delay: 0.5s;
}

.delay-2 {
  animation-delay: 1s;
}

@keyframes heartbeat {
  0%, 100% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.3;
  }
}

/* 数据流动效果 */
.data-stream {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.data-particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(59, 130, 246, 0.8);
  border-radius: 50%;
  animation: dataFlow 8s linear infinite;
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
}

.data-particle:nth-child(1) { left: 10%; top: 10%; }
.data-particle:nth-child(2) { left: 20%; top: 30%; }
.data-particle:nth-child(3) { left: 80%; top: 20%; }
.data-particle:nth-child(4) { left: 90%; top: 70%; }
.data-particle:nth-child(5) { left: 15%; top: 80%; }
.data-particle:nth-child(6) { left: 70%; top: 90%; }
.data-particle:nth-child(7) { left: 50%; top: 5%; }
.data-particle:nth-child(8) { left: 85%; top: 50%; }

@keyframes dataFlow {
  0% {
    transform: translateY(0) scale(0.5);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) scale(1.5);
    opacity: 0;
  }
}

/* AI智能网格背景 */
.ai-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.1;
}

.grid-line {
  position: absolute;
  background: rgba(59, 130, 246, 0.2);
}

.grid-line[class*="horizontal"] {
  width: 100%;
  height: 1px;
  animation: gridPulse 4s ease-in-out infinite;
}

.grid-line[class*="vertical"] {
  height: 100%;
  width: 1px;
  animation: gridPulse 4s ease-in-out infinite;
}

.horizontal-1 { top: 8.33%; animation-delay: 0s; }
.horizontal-2 { top: 16.66%; animation-delay: 0.3s; }
.horizontal-3 { top: 25%; animation-delay: 0.6s; }
.horizontal-4 { top: 33.33%; animation-delay: 0.9s; }
.horizontal-5 { top: 41.66%; animation-delay: 1.2s; }
.horizontal-6 { top: 50%; animation-delay: 1.5s; }
.horizontal-7 { top: 58.33%; animation-delay: 1.8s; }
.horizontal-8 { top: 66.66%; animation-delay: 2.1s; }
.horizontal-9 { top: 75%; animation-delay: 2.4s; }
.horizontal-10 { top: 83.33%; animation-delay: 2.7s; }
.horizontal-11 { top: 91.66%; animation-delay: 3s; }
.horizontal-12 { top: 100%; animation-delay: 3.3s; }

.vertical-1 { left: 8.33%; animation-delay: 0.1s; }
.vertical-2 { left: 16.66%; animation-delay: 0.4s; }
.vertical-3 { left: 25%; animation-delay: 0.7s; }
.vertical-4 { left: 33.33%; animation-delay: 1s; }
.vertical-5 { left: 41.66%; animation-delay: 1.3s; }
.vertical-6 { left: 50%; animation-delay: 1.6s; }
.vertical-7 { left: 58.33%; animation-delay: 1.9s; }
.vertical-8 { left: 66.66%; animation-delay: 2.2s; }
.vertical-9 { left: 75%; animation-delay: 2.5s; }
.vertical-10 { left: 83.33%; animation-delay: 2.8s; }
.vertical-11 { left: 91.66%; animation-delay: 3.1s; }
.vertical-12 { left: 100%; animation-delay: 3.4s; }

@keyframes gridPulse {
  0%, 100% {
    opacity: 0.1;
  }
  50% {
    opacity: 0.4;
  }
}

/* 主要内容区域 */
.login-main-content {
  position: relative;
  z-index: 2;
  display: flex;
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 100px rgba(59, 130, 246, 0.1);
  overflow: hidden;
}

/* 左侧健康概念展示 */
.health-showcase {
  flex: 1;
  padding: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  position: relative;
}

.health-icon-container {
  display: flex;
  gap: 30px;
  margin-bottom: 40px;
  justify-content: center;
}

.health-icon {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.heartrate {
  background: linear-gradient(45deg, #3b82f6, #1d4ed8);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
}

.ai-brain {
  background: linear-gradient(45deg, #8b5cf6, #7c3aed);
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3);
}

.data-chart {
  background: linear-gradient(45deg, #10b981, #059669);
  box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
}

.heartrate-svg, .brain-svg, .chart-svg {
  width: 40px;
  height: 40px;
  fill: white;
}

.pulse-line {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: white;
  animation: heartratePulse 1.5s ease-in-out infinite;
}

@keyframes heartratePulse {
  0%, 100% {
    width: 20px;
    opacity: 0.5;
  }
  50% {
    width: 60px;
    opacity: 1;
  }
}

.ai-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: white;
  border-radius: 50%;
  animation: aiFloat 3s ease-in-out infinite;
}

.particle:nth-child(1) { top: 20%; left: 20%; animation-delay: 0s; }
.particle:nth-child(2) { top: 80%; left: 30%; animation-delay: 0.5s; }
.particle:nth-child(3) { top: 40%; right: 25%; animation-delay: 1s; }
.particle:nth-child(4) { bottom: 30%; left: 60%; animation-delay: 1.5s; }
.particle:nth-child(5) { top: 60%; right: 40%; animation-delay: 2s; }
.particle:nth-child(6) { bottom: 20%; right: 20%; animation-delay: 2.5s; }

@keyframes aiFloat {
  0%, 100% {
    transform: translateY(0) scale(0.8);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-10px) scale(1.2);
    opacity: 1;
  }
}

.chart-bars {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 3px;
  height: 20px;
}

.bar {
  width: 4px;
  background: white;
  border-radius: 2px;
  animation: chartGrow 2s ease-in-out infinite;
}

@keyframes chartGrow {
  0%, 100% {
    height: 20%;
  }
  50% {
    height: 80%;
  }
}

.showcase-text {
  text-align: center;
  color: white;
}

.health-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.2;
  text-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
}

.gradient-text {
  background: linear-gradient(45deg, #3b82f6, #8b5cf6, #10b981, #06b6d4);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradientShift 3s ease-in-out infinite;
}

.normal-text {
  color: white;
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.health-subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin-bottom: 40px;
  line-height: 1.6;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 25px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 1.1rem;
  min-width: 220px;
  justify-content: flex-start;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateX(10px);
}

.feature-icon {
  font-size: 1.5rem;
  width: 30px;
  text-align: center;
}

/* 右侧登录表单区域 */
.login-form-section {
  flex: 0 0 480px;
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  position: relative;
  border-left: 1px solid rgba(59, 130, 246, 0.2);
}

.login-form-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 2px;
  height: 100%;
  background: linear-gradient(to bottom, transparent, #3b82f6, transparent);
  animation: borderScan 3s ease-in-out infinite;
}

@keyframes borderScan {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

.system-controls {
  padding: 30px 40px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2);
  background: rgba(15, 23, 42, 0.8);
}

.logo-title-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.system-logo {
  font-size: 2.5rem;
  color: #667eea;
}

.system-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.control-buttons {
  display: flex;
  gap: 15px;
}

.control-btn {
  padding: 8px;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  transition: all 0.3s ease;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.control-btn:hover {
  background: rgba(59, 130, 246, 0.3);
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
}

.login-card {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-title {
  font-size: 2rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 10px;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.title-decoration {
  width: 60px;
  height: 3px;
  background: linear-gradient(45deg, #3b82f6, #8b5cf6);
  margin: 0 auto;
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
  animation: decorationGlow 2s ease-in-out infinite alternate;
}

@keyframes decorationGlow {
  0% {
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
  }
  100% {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.8);
  }
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-main-content {
    flex-direction: column;
    width: 95vw;
    height: 90vh;
  }
  
  .health-showcase {
    flex: 0 0 40%;
    padding: 40px 30px;
  }
  
  .health-title {
    font-size: 2.5rem;
  }
  
  .health-icon-container {
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .health-icon {
    width: 60px;
    height: 60px;
  }
  
  .login-form-section {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .login-main-content {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }
  
  .health-showcase {
    flex: 0 0 35%;
    padding: 30px 20px;
  }
  
  .health-title {
    font-size: 2rem;
  }
  
  .health-subtitle {
    font-size: 1rem;
  }
  
  .health-icon-container {
    gap: 15px;
    margin-bottom: 20px;
  }
  
  .health-icon {
    width: 50px;
    height: 50px;
  }
  
  .feature-item {
    min-width: 180px;
    font-size: 1rem;
    padding: 12px 20px;
  }
  
  .system-controls {
    padding: 20px;
  }
  
  .system-title {
    font-size: 1.2rem;
  }
  
  .login-card {
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .health-showcase {
    padding: 20px 15px;
  }
  
  .health-title {
    font-size: 1.8rem;
  }
  
  .health-icon-container {
    flex-direction: row;
    justify-content: space-around;
    gap: 10px;
  }
  
  .health-icon {
    width: 45px;
    height: 45px;
  }
  
  .feature-list {
    gap: 15px;
  }
  
  .feature-item {
    min-width: 160px;
    font-size: 0.9rem;
    padding: 10px 15px;
  }
  
  .system-controls {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .logo-title-section {
    flex-direction: column;
    gap: 10px;
  }
  
  .login-card {
    padding: 20px 15px;
  }
}
</style>
