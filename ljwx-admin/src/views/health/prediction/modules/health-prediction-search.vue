<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { NButton, NCard, NForm, NFormItem, NInput, NSelect, NTreeSelect, NDatePicker } from 'naive-ui';
import { $t } from '@/locales';

defineOptions({
  name: 'HealthPredictionSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

interface Props {
  model: Api.Health.PredictionSearchParams;
  orgUnitsTree: Api.SystemManage.OrgUnitsTree[];
  userOptions: { label: string; value: string }[];
  customerId?: number;
}

const emit = defineEmits<Emits>();
const props = defineProps<Props>();

const model = defineModel<Api.Health.PredictionSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}

// 状态选项
const statusOptions = [
  { label: '全部', value: null },
  { label: '等待中', value: 'pending' },
  { label: '执行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
];

// 模型选项 (模拟数据，实际应该从API获取)
const modelOptions = [
  { label: '全部模型', value: null },
  { label: 'LSTM健康预测模型v2.1', value: 'lstm_v2_1' },
  { label: 'RandomForest风险评估模型v1.3', value: 'rf_v1_3' },
  { label: 'XGBoost综合预测模型v1.0', value: 'xgb_v1_0' },
  { label: 'CNN时序分析模型v2.0', value: 'cnn_v2_0' }
];

// 预测时长选项
const horizonOptions = [
  { label: '全部', value: null },
  { label: '1天', value: 1 },
  { label: '3天', value: 3 },
  { label: '7天', value: 7 },
  { label: '14天', value: 14 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 }
];

// 风险等级选项
const riskOptions = [
  { label: '全部', value: null },
  { label: '低风险', value: 'low' },
  { label: '中风险', value: 'medium' },
  { label: '高风险', value: 'high' }
];

// 准确率范围选项
const accuracyOptions = [
  { label: '全部', value: null },
  { label: '90%以上', value: '0.9+' },
  { label: '80%-90%', value: '0.8-0.9' },
  { label: '70%-80%', value: '0.7-0.8' },
  { label: '70%以下', value: '0.7-' }
];

// 组织树选项
const orgOptions = computed(() => 
  props.orgUnitsTree.map(item => ({
    key: item.id,
    label: item.name,
    value: item.id,
    children: item.children?.map(child => ({
      key: child.id,
      label: child.name,
      value: child.id
    }))
  }))
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <template #header>
      <div class="flex items-center">
        <div class="i-mdi:filter-variant mr-2 text-lg" />
        <span class="font-medium">搜索筛选</span>
      </div>
    </template>

    <NForm ref="queryFormRef" :model="model" label-placement="left" :label-width="80">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <!-- 任务名称 -->
        <NFormItem label="任务名称" path="name">
          <NInput v-model:value="model.name" clearable placeholder="请输入任务名称" />
        </NFormItem>

        <!-- 预测模型 -->
        <NFormItem label="预测模型" path="modelId">
          <NSelect 
            v-model:value="model.modelId" 
            :options="modelOptions" 
            clearable 
            placeholder="请选择预测模型" 
          />
        </NFormItem>

        <!-- 任务状态 -->
        <NFormItem label="任务状态" path="status">
          <NSelect 
            v-model:value="model.status" 
            :options="statusOptions" 
            clearable 
            placeholder="请选择任务状态" 
          />
        </NFormItem>

        <!-- 组织部门 -->
        <NFormItem label="所属部门" path="orgId">
          <NTreeSelect
            v-model:value="model.orgId"
            :options="orgOptions"
            clearable
            placeholder="请选择部门"
            key-field="value"
            label-field="label"
            children-field="children"
          />
        </NFormItem>

        <!-- 目标用户 -->
        <NFormItem label="目标用户" path="userId">
          <NSelect 
            v-model:value="model.userId" 
            :options="userOptions" 
            clearable 
            placeholder="请选择用户" 
          />
        </NFormItem>

        <!-- 预测时长 -->
        <NFormItem label="预测时长" path="predictionHorizon">
          <NSelect 
            v-model:value="model.predictionHorizon" 
            :options="horizonOptions" 
            clearable 
            placeholder="请选择时长" 
          />
        </NFormItem>

        <!-- 风险等级 -->
        <NFormItem label="风险等级" path="riskLevel">
          <NSelect 
            v-model:value="model.riskLevel" 
            :options="riskOptions" 
            clearable 
            placeholder="请选择风险等级" 
          />
        </NFormItem>

        <!-- 准确率范围 -->
        <NFormItem label="准确率" path="accuracyRange">
          <NSelect 
            v-model:value="model.accuracyRange" 
            :options="accuracyOptions" 
            clearable 
            placeholder="请选择准确率范围" 
          />
        </NFormItem>

        <!-- 创建日期范围 -->
        <NFormItem label="创建时间" path="dateRange" class="sm:col-span-2">
          <NDatePicker
            v-model:value="model.dateRange"
            type="daterange"
            clearable
            placeholder="请选择日期范围"
            format="yyyy-MM-dd"
            class="w-full"
          />
        </NFormItem>
      </div>

      <div class="flex-y-center justify-end gap-12px mt-4">
        <NButton @click="reset">
          <template #icon>
            <div class="i-mdi:refresh" />
          </template>
          {{ $t('common.reset') }}
        </NButton>
        <NButton type="primary" ghost @click="search">
          <template #icon>
            <div class="i-mdi:magnify" />
          </template>
          {{ $t('common.search') }}
        </NButton>
      </div>
    </NForm>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  --n-padding: 16px;
}

:deep(.n-form-item-label) {
  white-space: nowrap;
}

:deep(.n-date-picker) {
  width: 100%;
}
</style>