<template>
  <n-modal v-model:show="visible" preset="dialog" title="档案分析视图" style="width: 90%;">
    <div class="text-center p-8">
      <n-icon size="48" class="mb-4 text-primary">
        <icon-ic:baseline-analytics />
      </n-icon>
      <h3 class="text-lg font-medium mb-2">功能开发中</h3>
      <p class="text-gray-600">档案分析视图功能正在开发中</p>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

defineProps<{
  visible: boolean
  profileData?: any
}>()

defineEmits<{
  'update:visible': [value: boolean]
}>()
</script>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>