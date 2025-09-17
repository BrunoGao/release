<script setup lang="ts">
import { NButton, NDatePicker, NForm, NFormItem, NSelect, NSpace } from 'naive-ui';
import { computed, ref, watch } from 'vue';

defineOptions({
  name: 'HealthAnalysisSearch'
});

interface Props {
  model: {
    orgId: number | null;
    userId: string | null;
    startDate: string;
    endDate: string;
    customerId: number | undefined;
  };
  orgUnitsTree?: Api.SystemManage.OrgUnitsTree[];
  userOptions?: { label: string; value: string }[];
}

interface Emits {
  (e: 'update:model', value: Props['model']): void;
  (e: 'search'): void;
  (e: 'reset'): void;
}

const props = withDefaults(defineProps<Props>(), {
  orgUnitsTree: () => [],
  userOptions: () => []
});

const emit = defineEmits<Emits>();

const formModel = computed({
  get() {
    return props.model;
  },
  set(value) {
    emit('update:model', value);
  }
});

// 将树形数据转换为选项数组
const orgOptions = computed(() => {
  const convertTreeToOptions = (tree: Api.SystemManage.OrgUnitsTree[]): { label: string; value: number }[] => {
    const result: { label: string; value: number }[] = [];

    const traverse = (nodes: Api.SystemManage.OrgUnitsTree[], prefix = '') => {
      nodes.forEach(node => {
        result.push({
          label: prefix + node.name,
          value: node.id
        });

        if (node.children && node.children.length > 0) {
          traverse(node.children, `${prefix}└ `);
        }
      });
    };

    traverse(tree);
    return result;
  };

  return convertTreeToOptions(props.orgUnitsTree);
});

// 时间范围快捷选项
const timeRangeShortcuts = {
  今天: () => {
    const today = new Date();
    return [today, today];
  },
  最近7天: () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 6);
    return [start, end];
  },
  最近30天: () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 29);
    return [start, end];
  },
  最近3个月: () => {
    const end = new Date();
    const start = new Date();
    start.setMonth(start.getMonth() - 3);
    return [start, end];
  }
};

// 日期范围值
const dateRange = computed({
  get() {
    return [new Date(formModel.value.startDate).getTime(), new Date(formModel.value.endDate).getTime()];
  },
  set(value: [number, number] | null) {
    if (value) {
      formModel.value = {
        ...formModel.value,
        startDate: new Date(value[0]).toISOString().split('T')[0],
        endDate: new Date(value[1]).toISOString().split('T')[0]
      };
    }
  }
});

// 搜索处理
function handleSearch() {
  emit('search');
}

// 重置处理
function handleReset() {
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(today.getDate() - 30);

  formModel.value = {
    orgId: null,
    userId: null,
    startDate: thirtyDaysAgo.toISOString().split('T')[0],
    endDate: today.toISOString().split('T')[0],
    customerId: props.model.customerId
  };

  emit('reset');
  emit('search');
}

// 监听组织变化，清空用户选择
watch(
  () => formModel.value.orgId,
  () => {
    formModel.value.userId = null;
  }
);
</script>

<template>
  <NCard :bordered="false" class="search-card">
    <template #header>
      <div class="flex items-center gap-2">
        <div class="i-material-symbols:search text-lg text-blue-600"></div>
        <span class="font-medium">筛选条件</span>
      </div>
    </template>

    <NForm :model="formModel" label-width="80px" label-placement="left" class="search-form">
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-4 md:grid-cols-2">
        <!-- 组织选择 -->
        <NFormItem label="组织部门" class="search-item">
          <NSelect v-model:value="formModel.orgId" :options="orgOptions" placeholder="请选择组织部门" clearable filterable class="search-select" />
        </NFormItem>

        <!-- 用户选择 -->
        <NFormItem label="目标用户" class="search-item">
          <NSelect
            v-model:value="formModel.userId"
            :options="userOptions"
            placeholder="请选择用户"
            clearable
            filterable
            :disabled="!formModel.orgId"
            class="search-select"
          />
        </NFormItem>

        <!-- 时间范围 -->
        <NFormItem label="分析时段" class="search-item md:col-span-2">
          <NDatePicker
            v-model:value="dateRange"
            type="daterange"
            :shortcuts="timeRangeShortcuts"
            placeholder="选择分析时间段"
            format="yyyy-MM-dd"
            class="search-date-picker"
          />
        </NFormItem>
      </div>

      <!-- 操作按钮 -->
      <div class="mt-4 flex justify-end gap-3 border-t border-gray-100 pt-4">
        <NButton @click="handleReset">
          <template #icon>
            <div class="i-material-symbols:refresh"></div>
          </template>
          重置
        </NButton>
        <NButton type="primary" @click="handleSearch">
          <template #icon>
            <div class="i-material-symbols:analytics"></div>
          </template>
          开始分析
        </NButton>
      </div>
    </NForm>
  </NCard>
</template>

<style scoped>
.search-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 16px;
}

.search-form {
  margin: 0;
}

.search-item :deep(.n-form-item-label) {
  font-weight: 500;
  color: #374151;
}

.search-select,
.search-date-picker {
  width: 100%;
}

.search-select:hover,
.search-date-picker:hover {
  border-color: #3b82f6;
}

:deep(.n-date-picker .n-input) {
  border-radius: 6px;
}

:deep(.n-select .n-base-selection) {
  border-radius: 6px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 {
    grid-template-columns: 1fr;
  }

  .md\\:col-span-2 {
    grid-column: span 1;
  }
}
</style>
