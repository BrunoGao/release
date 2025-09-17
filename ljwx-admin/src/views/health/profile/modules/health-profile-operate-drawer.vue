<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';

defineProps<{
  visible: boolean;
  operateType?: string;
  editingData?: any;
}>();

defineEmits<{
  'update:visible': [value: boolean];
  submitted: [];
}>();
</script>

<template>
  <NDrawer v-model:show="visible" width="600">
    <NDrawerContent title="健康档案操作">
      <div class="p-8 text-center">
        <NIcon size="48" class="mb-4 text-primary">
          <icon-ic:baseline-construction />
        </NIcon>
        <h3 class="mb-2 text-lg font-medium">功能开发中</h3>
        <p class="text-gray-600">健康档案操作功能正在开发中</p>
      </div>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>
