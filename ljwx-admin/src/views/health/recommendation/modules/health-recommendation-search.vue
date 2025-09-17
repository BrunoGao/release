<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { NButton, NCard, NDatePicker, NForm, NFormItem, NInput, NSelect, NTreeSelect } from 'naive-ui';
import { $t } from '@/locales';

defineOptions({
  name: 'HealthRecommendationSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

interface Props {
  model: Api.Health.RecommendationSearchParams;
  orgUnitsTree: Api.SystemManage.OrgUnitsTree[];
  userOptions: { label: string; value: string }[];
  customerId?: number;
}

const emit = defineEmits<Emits>();
const props = defineProps<Props>();

const model = defineModel<Api.Health.RecommendationSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}

// 建议类型选项
const typeOptions = [
  { label: '全部类型', value: null },
  { label: '生活方式', value: 'lifestyle' },
  { label: '运动健身', value: 'exercise' },
  { label: '营养饮食', value: 'nutrition' },
  { label: '医疗建议', value: 'medical' },
  { label: '心理健康', value: 'mental' }
];

// 状态选项
const statusOptions = [
  { label: '全部状态', value: null },
  { label: '待发送', value: 'pending' },
  { label: '已发送', value: 'sent' },
  { label: '已查看', value: 'read' },
  { label: '已完成', value: 'completed' },
  { label: '已拒绝', value: 'rejected' }
];

// 优先级选项
const priorityOptions = [
  { label: '全部优先级', value: null },
  { label: '高优先级', value: 'high' },
  { label: '中优先级', value: 'medium' },
  { label: '低优先级', value: 'low' }
];

// 生成方式选项
const generationOptions = [
  { label: '全部方式', value: null },
  { label: 'AI生成', value: true },
  { label: '手动创建', value: false }
];

// 有效性评分选项
const effectivenessOptions = [
  { label: '全部评分', value: null },
  { label: '5分（非常有效）', value: '5' },
  { label: '4分（比较有效）', value: '4' },
  { label: '3分（一般有效）', value: '3' },
  { label: '2分（不太有效）', value: '2' },
  { label: '1分（无效）', value: '1' },
  { label: '未评分', value: 'null' }
];

// 健康评分范围选项
const healthScoreOptions = [
  { label: '全部评分', value: null },
  { label: '80分以上', value: '80+' },
  { label: '60-80分', value: '60-80' },
  { label: '60分以下', value: '60-' }
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
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-3 sm:grid-cols-2 xl:grid-cols-4">
        <!-- 建议标题/内容 -->
        <NFormItem label="建议内容" path="keyword">
          <NInput v-model:value="model.keyword" clearable placeholder="搜索标题或内容关键词" />
        </NFormItem>

        <!-- 目标用户 -->
        <NFormItem label="目标用户" path="userId">
          <NSelect v-model:value="model.userId" :options="userOptions" clearable filterable placeholder="请选择用户" />
        </NFormItem>

        <!-- 建议类型 -->
        <NFormItem label="建议类型" path="recommendationType">
          <NSelect v-model:value="model.recommendationType" :options="typeOptions" clearable placeholder="请选择建议类型" />
        </NFormItem>

        <!-- 建议状态 -->
        <NFormItem label="建议状态" path="status">
          <NSelect v-model:value="model.status" :options="statusOptions" clearable placeholder="请选择状态" />
        </NFormItem>

        <!-- 优先级 -->
        <NFormItem label="优先级" path="priority">
          <NSelect v-model:value="model.priority" :options="priorityOptions" clearable placeholder="请选择优先级" />
        </NFormItem>

        <!-- 生成方式 -->
        <NFormItem label="生成方式" path="aiGenerated">
          <NSelect v-model:value="model.aiGenerated" :options="generationOptions" clearable placeholder="请选择生成方式" />
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

        <!-- 有效性评分 -->
        <NFormItem label="有效性评分" path="effectivenessScore">
          <NSelect v-model:value="model.effectivenessScore" :options="effectivenessOptions" clearable placeholder="请选择评分" />
        </NFormItem>

        <!-- 健康评分范围 -->
        <NFormItem label="健康评分" path="healthScoreRange">
          <NSelect v-model:value="model.healthScoreRange" :options="healthScoreOptions" clearable placeholder="请选择评分范围" />
        </NFormItem>

        <!-- 创建时间范围 -->
        <NFormItem label="创建时间" path="dateRange" class="sm:col-span-2">
          <NDatePicker v-model:value="model.dateRange" type="daterange" clearable placeholder="请选择日期范围" format="yyyy-MM-dd" class="w-full" />
        </NFormItem>

        <!-- 发送时间范围 -->
        <NFormItem label="发送时间" path="sendDateRange" class="sm:col-span-2">
          <NDatePicker
            v-model:value="model.sendDateRange"
            type="daterange"
            clearable
            placeholder="请选择发送日期范围"
            format="yyyy-MM-dd"
            class="w-full"
          />
        </NFormItem>
      </div>

      <div class="mt-4 flex-y-center justify-end gap-12px">
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
