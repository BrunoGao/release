<template>
  <div v-if="showTenantInfo" class="tenant-info">
    <div class="tenant-badge">
      <SvgIcon icon="mdi:domain" class="text-blue-500" />
      <span class="tenant-text">
        <span class="label">当前租户:</span>
        <span class="tenant-name">{{ currentCustomer?.name || '未选择' }}</span>
        <span v-if="currentCustomer?.id" class="tenant-id">(ID: {{ currentCustomer.id }})</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import SvgIcon from '@/components/custom/svg-icon.vue';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomerStore } from '@/store/modules/customer';

defineOptions({
  name: 'TenantInfo'
});

const authStore = useAuthStore();
const customerStore = useCustomerStore();

// 当前客户信息
const currentCustomer = computed(() => customerStore.currentCustomer);

// 是否显示租户信息（只有admin用户才显示）
const showTenantInfo = computed(() => {
  return authStore.userInfo?.userName === 'admin' && customerStore.canSwitchCustomer;
});

// 调试信息
watchEffect(() => {
  console.log('[TenantInfo] 状态更新:', {
    showTenantInfo: showTenantInfo.value,
    currentCustomer: currentCustomer.value,
    currentCustomerId: customerStore.currentCustomerId,
    userName: authStore.userInfo?.userName,
    canSwitch: customerStore.canSwitchCustomer
  });
});
</script>

<style scoped>
.tenant-info {
  @apply flex items-center;
}

.tenant-badge {
  @apply flex items-center px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700;
  @apply text-sm font-medium;
}

.tenant-text {
  @apply ml-2 flex items-center space-x-1;
}

.label {
  @apply text-gray-600 dark:text-gray-400;
}

.tenant-name {
  @apply text-blue-700 dark:text-blue-300 font-semibold;
}

.tenant-id {
  @apply text-gray-500 dark:text-gray-400 text-xs;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tenant-badge {
    @apply px-2 py-1 text-xs;
  }
  
  .tenant-id {
    @apply hidden;
  }
}
</style>