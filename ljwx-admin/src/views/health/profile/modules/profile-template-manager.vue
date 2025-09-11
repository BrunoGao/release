<template>
  <n-modal v-model:show="visible" preset="dialog" title="档案模板管理" style="width: 80%;">
    <div class="text-center p-8">
      <n-icon size="48" class="mb-4 text-primary">
        <icon-ic:baseline-description />
      </n-icon>
      <h3 class="text-lg font-medium mb-2">功能开发中</h3>
      <p class="text-gray-600">档案模板管理功能正在开发中</p>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

defineProps<{
  visible: boolean
}>()

defineEmits<{
  'update:visible': [value: boolean]
  'template-selected': [template: any]
}>()
</script>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>