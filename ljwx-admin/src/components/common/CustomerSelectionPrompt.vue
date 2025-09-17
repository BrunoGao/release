<script setup lang="ts">
import { computed } from 'vue';
import { NAlert, NButton, NSpace } from 'naive-ui';
import { useCustomer } from '@/hooks/business/customer';

defineOptions({
  name: 'CustomerSelectionPrompt'
});

const { isAdmin, needsCustomerSelection, currentCustomer } = useCustomer();

// 是否显示选择提示
const showPrompt = computed(() => {
  return isAdmin.value && needsCustomerSelection.value;
});
</script>

<template>
  <div v-if="showPrompt" class="customer-selection-prompt">
    <NAlert type="info" :bordered="false" :show-icon="true" class="mb-4">
      <template #header>请选择要管理的客户</template>

      <div>
        <p class="mb-3">您当前以超级管理员身份登录，请先选择要管理的客户，然后开始使用系统功能。</p>

        <NSpace>
          <div class="text-sm text-gray-500">💡 提示：您可以在页面右上角的客户切换器中选择客户</div>
        </NSpace>
      </div>
    </NAlert>
  </div>
</template>

<style scoped>
.customer-selection-prompt {
  @apply w-full max-w-2xl mx-auto;
}

:deep(.n-alert) {
  @apply rounded-lg border-l-4 border-l-blue-500;
}

:deep(.n-alert .n-alert__icon) {
  @apply text-blue-500;
}
</style>
