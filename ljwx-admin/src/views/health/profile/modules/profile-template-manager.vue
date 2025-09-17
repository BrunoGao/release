<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';

defineProps<{
  visible: boolean;
}>();

defineEmits<{
  'update:visible': [value: boolean];
  'template-selected': [template: any];
}>();
</script>

<template>
  <NModal v-model:show="visible" preset="dialog" title="档案模板管理" style="width: 80%">
    <div class="p-8 text-center">
      <NIcon size="48" class="mb-4 text-primary">
        <icon-ic:baseline-description />
      </NIcon>
      <h3 class="mb-2 text-lg font-medium">功能开发中</h3>
      <p class="text-gray-600">档案模板管理功能正在开发中</p>
    </div>
  </NModal>
</template>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>
