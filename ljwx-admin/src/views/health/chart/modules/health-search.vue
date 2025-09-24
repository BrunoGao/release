<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { $t } from '@/locales';
import { useNaiveForm } from '@/hooks/common/form';
import { useDict } from '@/hooks/business/dict';
import { fetchBaseFeatures } from '@/service/api/health';

defineOptions({
  name: 'HealthChartSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

interface Props {
  orgUnitsTree: Array<any>;
  userOptions: Array<any>;
  customerId: number;
}

const props = defineProps<Props>();

const emit = defineEmits<Emits>();

const { formRef, restoreValidation } = useNaiveForm();
const { dictOptions } = useDict();

const model = defineModel<Api.Health.HealthChartSearchParams>('model', { required: true });

// 特征选项
const featureOptions = ref<Array<{ label: string; value: string }>>([]);

// 获取基础特征
async function loadFeatureOptions() {
  console.log('🔄 加载特征选项 - customerId:', props.customerId);

  try {
    const response = await fetchBaseFeatures(props.customerId);
    if (response && response.data) {
      featureOptions.value = [{ label: '全部', value: 'all' }, ...response.data];
      console.log('✅ 加载特征选项成功:', featureOptions.value);
    }
  } catch (error) {
    console.error('❌ 加载特征选项失败:', error);
    // 使用默认选项作为后备
    featureOptions.value = [
      { label: '全部', value: 'all' },
      { label: '心率', value: 'heart_rate' },
      { label: '血氧', value: 'blood_oxygen' },
      { label: '体温', value: 'temperature' },
      { label: '压力', value: 'stress' },
      { label: '睡眠', value: 'sleep' },
      { label: '步数', value: 'step' },
      { label: '距离', value: 'distance' },
      { label: '卡路里', value: 'calorie' }
    ];
  }
}

async function reset() {
  await restoreValidation();
  emit('reset');
}

function search() {
  emit('search');
}

// 监听dataType变化，如果选择全部则设置为null
watch(
  () => model.value.dataType,
  dataType_val => {
    if (dataType_val === 'all') model.value.dataType = null;
  }
);

// 监听orgId变化处理数组选择
watch(
  () => model.value.orgId,
  orgId_val => {
    // 如果orgId是数组（多选），保持数组形式；如果是单选，保持单值形式
    // 这里不需要额外处理，直接保持原值即可
  },
  { immediate: true }
);

// 组件挂载时加载特征选项
onMounted(() => {
  loadFeatureOptions();
});
</script>

<template>
  <NCard :title="$t('common.search')" :bordered="false" size="small" class="card-wrapper">
    <NForm ref="formRef" :model="model" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="orgId">
          <NTreeSelect
            v-model:value="model.orgId"
            size="small"
            checkable
            filterable
            key-field="id"
            label-field="name"
            default-expand-all
            :max-tag-count="7"
            :placeholder="$t('page.health.device.message.form.departmentName')"
            :options="props.orgUnitsTree"
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userId">
          <NSelect
            v-model:value="model.userId"
            size="small"
            :placeholder="$t('page.health.device.message.form.userName')"
            :options="props.userOptions"
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.dataType')" path="dataType" class="pr-24px">
          <NSelect
            v-model:value="model.dataType"
            :placeholder="$t('page.health.chart.dataType')"
            :options="featureOptions"
            :loading="featureOptions.length === 0"
          />
        </NFormItemGi>

        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.startDate')" path="startDate" class="pr-24px">
          <NDatePicker v-model:value="model.startDate" :placeholder="$t('page.health.chart.startDate')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.endDate')" path="endDate" class="pr-24px">
          <NDatePicker v-model:value="model.endDate" :placeholder="$t('page.health.chart.endDate')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.timeType')" path="timeType" class="pr-24px">
          <NSelect v-model:value="model.timeType" :placeholder="$t('page.health.chart.timeType')" :options="dictOptions('time_type')" />
        </NFormItemGi>
        <NFormItemGi span="24 m:12" class="pr-24px">
          <NSpace class="w-full" justify="end">
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="primary" ghost @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>
          </NSpace>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 20px !important;
  backdrop-filter: blur(25px) !important;
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.03) 0%, rgba(255, 0, 170, 0.03) 100%);
  border-radius: 20px;
  pointer-events: none;
  z-index: 0;
}

.card-wrapper:hover {
  border-color: rgba(0, 245, 255, 0.4) !important;
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 30px rgba(0, 245, 255, 0.15) !important;
}

.card-wrapper:hover::before {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.08) 0%, rgba(255, 0, 170, 0.08) 100%);
}

/* 覆盖卡片头部样式 */
:deep(.n-card-header) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
  backdrop-filter: blur(10px) !important;
  position: relative;
  z-index: 1;
}

:deep(.n-card-header__main) {
  color: rgba(255, 255, 255, 0.95) !important;
  font-weight: 700 !important;
  font-size: 18px !important;
  letter-spacing: 0.5px !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 卡片内容区域 */
:deep(.n-card__content) {
  position: relative;
  z-index: 1;
  background: transparent !important;
}

/* 表单标签样式增强 */
:deep(.n-form-item-label__text) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  letter-spacing: 0.3px !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 输入框和选择器样式 */
:deep(.n-input),
:deep(.n-select),
:deep(.n-tree-select),
:deep(.n-date-picker) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(10px) !important;
  transition: all 0.3s ease !important;
}

:deep(.n-input:hover),
:deep(.n-select:hover),
:deep(.n-tree-select:hover),
:deep(.n-date-picker:hover) {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: rgba(0, 245, 255, 0.5) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

:deep(.n-input:focus-within),
:deep(.n-select:focus-within),
:deep(.n-tree-select:focus-within),
:deep(.n-date-picker:focus-within) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(0, 245, 255, 0.8) !important;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.2),
    0 0 0 2px rgba(0, 245, 255, 0.2) !important;
}

/* 输入框文字样式 */
:deep(.n-input__input-el),
:deep(.n-base-selection-input-tag),
:deep(.n-base-selection-placeholder),
:deep(.n-base-selection-single-value),
:deep(.n-date-picker-trigger__input) {
  color: rgba(255, 255, 255, 0.95) !important;
  font-weight: 500 !important;
}

:deep(.n-input__placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

/* 选择器箭头图标 */
:deep(.n-base-selection-suffix),
:deep(.n-base-suffix) {
  color: rgba(255, 255, 255, 0.7) !important;
}

/* 按钮样式增强 */
:deep(.n-button) {
  border-radius: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(10px) !important;
}

:deep(.n-button--default-type) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

:deep(.n-button--default-type:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(0, 245, 255, 0.5) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
}

:deep(.n-button--primary-type) {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.8), rgba(255, 0, 170, 0.8)) !important;
  border: 1px solid rgba(0, 245, 255, 0.6) !important;
  color: rgba(255, 255, 255, 0.95) !important;
  box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3) !important;
}

:deep(.n-button--primary-type:hover) {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.9), rgba(255, 0, 170, 0.9)) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(0, 245, 255, 0.4) !important;
}

/* 图标样式 */
:deep(.text-icon) {
  color: inherit !important;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

/* 响应式优化 */
@media (max-width: 768px) {
  :deep(.n-form-item-label__text) {
    font-size: 13px !important;
  }
  
  :deep(.n-card-header__main) {
    font-size: 16px !important;
  }
  
  .card-wrapper {
    border-radius: 16px !important;
    margin: 0 -8px;
  }
  
  .card-wrapper::before {
    border-radius: 16px;
  }
}

/* 下拉面板样式 */
:deep(.n-base-select-menu) {
  background: rgba(30, 30, 60, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

:deep(.n-base-select-option) {
  color: rgba(255, 255, 255, 0.9) !important;
  transition: all 0.2s ease !important;
}

:deep(.n-base-select-option:hover) {
  background: rgba(0, 245, 255, 0.15) !important;
  color: rgba(255, 255, 255, 1) !important;
}

:deep(.n-base-select-option--selected) {
  background: rgba(0, 245, 255, 0.25) !important;
  color: rgba(255, 255, 255, 1) !important;
}
</style>
