<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/store/modules/auth';
import { request } from '@/service/request';

defineOptions({ name: 'SystemLogo' });

const authStore = useAuthStore();
const customLogoUrl = ref<string>('');
const useCustomLogo = ref(false);

// 获取当前用户的自定义logo
async function fetchCustomLogo() {
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

onMounted(() => {
  fetchCustomLogo();
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
