<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/store/modules/auth';
import { request } from '@/service/request';

defineOptions({ name: 'SystemLogo' });

const authStore = useAuthStore();
const customLogoUrl = ref<string>('');
const useCustomLogo = ref(false);

// 检查部署时注入的自定义logo配置
function checkDeploymentCustomLogo() {
  try {
    // 检查全局配置对象
    const logoConfig = (window as any).CUSTOM_LOGO_CONFIG;
    if (logoConfig && logoConfig.enabled && logoConfig.logoUrl) {
      console.log('检测到部署时的自定义logo配置:', logoConfig);
      
      // 验证logo文件是否可访问
      const img = new Image();
      img.onload = () => {
        customLogoUrl.value = logoConfig.logoUrl + '?t=' + (logoConfig.timestamp || Date.now());
        useCustomLogo.value = true;
        console.log('部署自定义logo加载成功:', customLogoUrl.value);
      };
      img.onerror = () => {
        console.warn('部署自定义logo文件无法访问，尝试其他方式');
        fetchCustomLogoFromAPI();
      };
      img.src = logoConfig.logoUrl + '?t=' + (logoConfig.timestamp || Date.now());
      return true;
    }
  } catch (error) {
    console.log('未检测到部署自定义logo配置，使用默认方式');
  }
  return false;
}

// 从API获取当前用户的自定义logo（原有逻辑）
async function fetchCustomLogoFromAPI() {
  try {
    const customerId = authStore.userInfo?.customerId;
    
    if (customerId !== undefined && customerId !== null) {
      // 直接尝试加载logo图片
      const logoImageUrl = `/t_customer_config/logo/${customerId}?t=${Date.now()}`;
      
      // 先尝试加载图片，如果成功就使用，失败就用默认
      const img = new Image();
      img.onload = () => {
        customLogoUrl.value = logoImageUrl;
        useCustomLogo.value = true;
      };
      img.onerror = () => {
        useCustomLogo.value = false;
      };
      img.src = logoImageUrl;
      
    } else {
      useCustomLogo.value = false;
    }
  } catch (error) {
    console.error('获取自定义logo失败:', error);
    useCustomLogo.value = false;
  }
}

// 获取自定义logo的主函数
async function fetchCustomLogo() {
  // 优先检查部署时的自定义logo配置
  if (!checkDeploymentCustomLogo()) {
    // 如果没有部署配置，则使用API方式
    await fetchCustomLogoFromAPI();
  }
}

onMounted(() => {
  fetchCustomLogo();
  
  // 监听logo配置更新事件（支持动态更新）
  window.addEventListener('customLogoConfigUpdated', () => {
    console.log('收到logo配置更新事件');
    fetchCustomLogo();
  });
});
</script>

<template>
  <!-- 如果有自定义logo就显示图片，否则显示默认图标 -->
  <div v-if="useCustomLogo" class="flex items-center justify-center">
    <img 
      :src="customLogoUrl" 
      alt="系统Logo" 
      class="max-w-full max-h-full object-contain"
      style="width: 1em; height: 1em;"
      @error="useCustomLogo = false"
    />
  </div>
  <icon-local-logo v-else />
</template>

<style scoped></style>
