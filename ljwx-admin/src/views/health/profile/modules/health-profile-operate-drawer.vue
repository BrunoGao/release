<template>
  <n-drawer v-model:show="visible" width="600">
    <n-drawer-content title="健康档案操作">
      <div class="text-center p-8">
        <n-icon size="48" class="mb-4 text-primary">
          <icon-ic:baseline-construction />
        </n-icon>
        <h3 class="text-lg font-medium mb-2">功能开发中</h3>
        <p class="text-gray-600">健康档案操作功能正在开发中</p>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

defineProps<{
  visible: boolean
  operateType?: string
  editingData?: any
}>()

defineEmits<{
  'update:visible': [value: boolean]
  'submitted': []
}>()
</script>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>