<script setup lang="ts">
import { NRadioButton, NRadioGroup } from 'naive-ui';
import { computed } from 'vue';

interface Props {
  value: Api.SystemManage.ViewMode;
  loading?: boolean;
}

interface Emits {
  (e: 'update:value', value: Api.SystemManage.ViewMode): void;
  (e: 'change', value: Api.SystemManage.ViewMode): void;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
});

const emit = defineEmits<Emits>();

const viewMode = computed({
  get() {
    return props.value;
  },
  set(value: Api.SystemManage.ViewMode) {
    emit('update:value', value);
    emit('change', value);
  }
});

const viewModeOptions = [
  {
    value: 'all' as const,
    label: '全部用户',
    icon: 'i-mdi:account-group',
    color: 'primary'
  },
  {
    value: 'employee' as const,
    label: '员工',
    icon: 'i-mdi:account',
    color: 'success'
  },
  {
    value: 'admin' as const,
    label: '管理员',
    icon: 'i-mdi:account-star',
    color: 'error'
  }
];
</script>

<template>
  <div class="view-mode-selector">
    <NRadioGroup v-model:value="viewMode" :disabled="loading" size="small" type="button">
      <template v-for="option in viewModeOptions" :key="option.value">
        <NRadioButton :value="option.value" class="view-mode-button">
          <div class="flex items-center gap-1">
            <div class="text-icon" :class="[option.icon]" />
            <span>{{ option.label }}</span>
          </div>
        </NRadioButton>
      </template>
    </NRadioGroup>
  </div>
</template>

<style scoped>
.view-mode-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-mode-button {
  min-width: 80px;
  justify-content: center;
}

.text-icon {
  width: 16px;
  height: 16px;
}
</style>
