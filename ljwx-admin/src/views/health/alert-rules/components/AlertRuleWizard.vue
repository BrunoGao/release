<template>
  <div class="alert-rule-wizard">
    <n-card title="告警规则配置向导">
      <div class="text-center p-8">
        <n-icon size="48" class="mb-4 text-primary">
          <icon-ic:baseline-construction />
        </n-icon>
        <h3 class="text-lg font-medium mb-2">功能开发中</h3>
        <p class="text-gray-600 mb-4">告警规则配置向导正在开发中，敬请期待</p>
        <n-space justify="center">
          <n-button @click="$emit('update:visible', false)">关闭</n-button>
          <n-button type="primary" @click="handleSave">保存</n-button>
        </n-space>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'

defineProps<{
  visible: boolean
  editRule?: any
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': []
}>()

const handleSave = () => {
  emit('success')
  emit('update:visible', false)
}
</script>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>