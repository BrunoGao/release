<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';

defineProps<{
  visible: boolean;
  editRule?: any;
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  success: [];
}>();

const handleSave = () => {
  emit('success');
  emit('update:visible', false);
};
</script>

<template>
  <div class="alert-rule-wizard">
    <NCard title="告警规则配置向导">
      <div class="p-8 text-center">
        <NIcon size="48" class="mb-4 text-primary">
          <icon-ic:baseline-construction />
        </NIcon>
        <h3 class="mb-2 text-lg font-medium">功能开发中</h3>
        <p class="mb-4 text-gray-600">告警规则配置向导正在开发中，敬请期待</p>
        <NSpace justify="center">
          <NButton @click="$emit('update:visible', false)">关闭</NButton>
          <NButton type="primary" @click="handleSave">保存</NButton>
        </NSpace>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>
