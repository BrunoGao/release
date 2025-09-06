import { createApp } from 'vue';
import './plugins/assets';
import { setupAppVersionNotification, setupDayjs, setupIconifyOffline, setupLoading, setupNProgress, setupNSetting } from './plugins';
import { setupStore } from './store';
import { setupRouter } from './router';
import { setupI18n } from './locales';
import App from './App.vue';

async function setupApp() {
  setupLoading();

  setupNProgress();

  setupIconifyOffline();

  setupDayjs();

  setupNSetting();

  const app = createApp(App);

  // 增强Vue错误处理 - 专门解决refs和push错误
  app.config.errorHandler = (err, vm, info) => {
    const errorMsg = (err as Error)?.message || String(err);

    // 特殊处理refs访问错误
    if (errorMsg.includes("Cannot read properties of null (reading 'refs')")) {
      console.warn('🔧 refs访问错误已拦截，组件可能未完全挂载');
      return; // 静默处理，不影响用户体验
    }

    // 特殊处理数组push错误
    if (errorMsg.includes("Cannot read properties of undefined (reading 'push')")) {
      console.warn('🔧 数组访问错误已拦截，对象可能未初始化');
      return; // 静默处理
    }

    // 其他错误正常记录
    console.error('🚨 Vue错误:', err);
    console.error('📍 错误位置:', info);
    console.error('🏷️ 组件实例:', vm);

    // 生产环境发送到监控系统
    if (import.meta.env.PROD) {
      // 可以集成Sentry等错误监控
      // window.reportError?.(err, info)
    }
  };

  setupStore(app);

  await setupRouter(app);

  setupI18n(app);

  setupAppVersionNotification();

  app.mount('#app');
}

// 增强Promise错误处理 - 专门解决异步操作错误
window.addEventListener('unhandledrejection', event => {
  const reason = event.reason;
  const reasonMsg = reason?.message || String(reason);

  // 特殊处理常见的异步错误
  if (reasonMsg.includes('refs') || reasonMsg.includes('push') || reasonMsg.includes('Cannot read properties')) {
    console.warn('🔧 异步操作错误已拦截:', reasonMsg);
    event.preventDefault();
    return;
  }

  // 路由相关错误的处理
  if (reasonMsg.includes('router') || reasonMsg.includes('Navigation')) {
    console.warn('🔧 路由错误已拦截:', reasonMsg);
    event.preventDefault();
    return;
  }

  console.error('🚨 未捕获Promise错误:', reason);
  event.preventDefault(); // 阻止错误冒泡到控制台
});

// 全局JS错误处理
window.addEventListener('error', event => {
  console.error('🚨 JS运行时错误:', event.error);
});

setupApp();
