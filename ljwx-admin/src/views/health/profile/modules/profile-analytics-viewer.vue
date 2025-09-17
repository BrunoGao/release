<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';

defineProps<{
  visible: boolean;
  profileData?: any;
}>();

defineEmits<{
  'update:visible': [value: boolean];
}>();
</script>

<template>
  <NModal v-model:show="visible" preset="dialog" title="档案分析视图" style="width: 90%">
    <div class="p-8 text-center">
      <NIcon size="48" class="mb-4 text-primary">
        <icon-ic:baseline-analytics />
      </NIcon>
      <h3 class="mb-2 text-lg font-medium">功能开发中</h3>
      <p class="text-gray-600">档案分析视图功能正在开发中</p>
    </div>
  </NModal>
</template>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>
