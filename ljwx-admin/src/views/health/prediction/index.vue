<script setup lang="tsx">
import { NButton, NPopconfirm, NProgress, NSpace, NTag } from 'naive-ui';
import { type Ref, computed, h, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import { convertToBeijingTime } from '@/utils/date';
import HealthPredictionSearch from './modules/health-prediction-search.vue';
import HealthPredictionOperateDrawer from './modules/health-prediction-operate-drawer.vue';
import PredictionModelManager from './modules/prediction-model-manager.vue';
import PredictionResultViewer from './modules/prediction-result-viewer.vue';
import AiModelsManagement from '../ai-models/index.vue';

defineOptions({
  name: 'HealthPredictionPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');
const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.PredictionTask | null> = ref(null);
const modelManagerVisible = ref(false);
const resultViewerVisible = ref(false);
const selectedTaskResult = ref(null);
const aiPredictionVisible = ref(false);

// 模拟 API 调用函数 - 实际应该从 service/api 导入
const fetchGetPredictionTaskList = async (params: any) => {
  // 模拟延迟
  await new Promise(resolve => setTimeout(resolve, 1000));

  // 模拟数据
  const mockTasks = [
    {
      id: '1',
      name: '用户健康风险预测',
      modelName: 'LSTM健康预测模型v2.1',
      targetUsers: 'all',
      predictionHorizon: 7,
      features: ['heart_rate', 'blood_oxygen', 'temperature'],
      status: 'completed',
      progress: 100,
      accuracy: 0.85,
      createdAt: '2024-01-20 10:30:00',
      completedAt: '2024-01-20 12:45:00',
      orgName: '技术部',
      userName: '全体用户',
      riskLevel: 'medium'
    },
    {
      id: '2',
      name: '心血管疾病风险评估',
      modelName: 'RandomForest风险评估模型v1.3',
      targetUsers: ['user1', 'user2'],
      predictionHorizon: 30,
      features: ['heart_rate', 'pressure_high', 'pressure_low'],
      status: 'running',
      progress: 65,
      accuracy: null,
      createdAt: '2024-01-21 09:15:00',
      completedAt: null,
      orgName: '销售部',
      userName: '张三, 李四',
      riskLevel: 'high'
    }
  ];

  return {
    error: null,
    data: {
      records: mockTasks,
      total: mockTasks.length,
      page: params.page || 1,
      pageSize: params.pageSize || 20
    }
  };
};

const fetchDeletePredictionTask = async (ids: string[]) => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return { error: null, data: { success: true } };
};

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetPredictionTaskList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    status: null,
    modelId: null,
    startDate,
    endDate
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'name',
      title: '任务名称',
      align: 'center',
      minWidth: 150
    },
    {
      key: 'modelName',
      title: '预测模型',
      align: 'center',
      minWidth: 200
    },
    {
      key: 'status',
      title: '状态',
      align: 'center',
      width: 100,
      render: row => {
        const statusMap = {
          pending: { type: 'warning', text: '等待中' },
          running: { type: 'info', text: '执行中' },
          completed: { type: 'success', text: '已完成' },
          failed: { type: 'error', text: '失败' }
        } as const;
        const status = statusMap[row.status as keyof typeof statusMap];
        return h(NTag, { type: status.type }, () => status.text);
      }
    },
    {
      key: 'progress',
      title: '进度',
      align: 'center',
      width: 120,
      render: row => {
        return h(NProgress, {
          percentage: row.progress,
          status: row.status === 'failed' ? 'error' : 'default',
          showIndicator: false
        });
      }
    },
    {
      key: 'predictionHorizon',
      title: '预测时长',
      align: 'center',
      width: 100,
      render: row => `${row.predictionHorizon}天`
    },
    {
      key: 'accuracy',
      title: '准确率',
      align: 'center',
      width: 100,
      render: row => {
        if (row.accuracy === null || row.status !== 'completed') {
          return '-';
        }
        return `${(row.accuracy * 100).toFixed(1)}%`;
      }
    },
    {
      key: 'riskLevel',
      title: '风险等级',
      align: 'center',
      width: 100,
      render: row => {
        const riskMap = {
          low: { type: 'success', text: '低风险' },
          medium: { type: 'warning', text: '中风险' },
          high: { type: 'error', text: '高风险' }
        } as const;
        const risk = riskMap[row.riskLevel as keyof typeof riskMap];
        return h(NTag, { type: risk.type }, () => risk.text);
      }
    },
    {
      key: 'createdAt',
      title: '创建时间',
      align: 'center',
      width: 160,
      render: row => convertToBeijingTime(row.createdAt)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 250,
      minWidth: 250,
      render: row => (
        <NSpace size="small">
          {row.status === 'completed' && (
            <NButton type="info" quaternary size="small" onClick={() => viewResults(row)}>
              查看结果
            </NButton>
          )}
          {hasAuth('health:prediction:edit') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('health:prediction:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" quaternary size="small">
                    {$t('common.delete')}
                  </NButton>
                )
              }}
            </NPopconfirm>
          )}
        </NSpace>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  operateType.value = 'add';
  editingData.value = null;
  openDrawer();
}

function edit(item: Api.Health.PredictionTask) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

function viewResults(task: Api.Health.PredictionTask) {
  selectedTaskResult.value = task;
  resultViewerVisible.value = true;
}

function openModelManager() {
  modelManagerVisible.value = true;
}

function openAiPrediction() {
  aiPredictionVisible.value = true;
}

async function handleDelete(id: string) {
  const { error, data: result } = await fetchDeletePredictionTask([id]);
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  const { error, data: result } = await fetchDeletePredictionTask(checkedRowKeys.value);
  if (!error && result) {
    await onBatchDeleted();
  }
}

// 组织架构和用户选项
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
      if (treeData.length > 0) {
        handleBindUsersByOrgId(treeData[0].id).then(result => {
          if (Array.isArray(result)) {
            userOptions.value = result;
          }
        });
      }
    }
  });
}

// 监听部门变化，更新员工列表
watch(
  () => searchParams.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

onMounted(() => {
  handleInitOptions();
});

// 统计信息
const taskStats = computed(() => {
  const stats = {
    total: data.value.length,
    completed: 0,
    running: 0,
    failed: 0,
    avgAccuracy: 0
  };

  let totalAccuracy = 0;
  let completedCount = 0;

  data.value.forEach(task => {
    if (task.status === 'completed') {
      stats.completed++;
      if (task.accuracy) {
        totalAccuracy += task.accuracy;
        completedCount++;
      }
    } else if (task.status === 'running') {
      stats.running++;
    } else if (task.status === 'failed') {
      stats.failed++;
    }
  });

  stats.avgAccuracy = completedCount > 0 ? totalAccuracy / completedCount : 0;
  return stats;
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 mb-4 gap-4 lg:grid-cols-4 sm:grid-cols-2">
      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">总任务数</div>
            <div class="text-2xl text-primary font-bold">{{ taskStats.total }}</div>
          </div>
          <div class="text-3xl text-primary opacity-20">📊</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">已完成</div>
            <div class="text-2xl text-success font-bold">{{ taskStats.completed }}</div>
          </div>
          <div class="text-3xl text-success opacity-20">✅</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">执行中</div>
            <div class="text-2xl text-info font-bold">{{ taskStats.running }}</div>
          </div>
          <div class="text-3xl text-info opacity-20">⚡</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">平均准确率</div>
            <div class="text-2xl text-warning font-bold">{{ (taskStats.avgAccuracy * 100).toFixed(1) }}%</div>
          </div>
          <div class="text-3xl text-warning opacity-20">🎯</div>
        </div>
      </NCard>
    </div>

    <!-- 搜索组件 -->
    <HealthPredictionSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      :customer-id="customerId"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />

    <!-- 主要内容区域 -->
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-semibold">健康预测任务管理</span>
          <NSpace>
            <NButton type="info" @click="openModelManager">
              <template #icon>
                <div class="i-mdi:brain" />
              </template>
              模型管理
            </NButton>
            <NButton type="success" @click="openAiPrediction">
              <template #icon>
                <div class="i-mdi:robot" />
              </template>
              AI预测
            </NButton>
          </NSpace>
        </div>
      </template>

      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="health:prediction:add"
        delete-auth="health:prediction:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #default>
          <NButton type="primary" @click="handleAdd">
            <template #icon>
              <div class="i-mdi:plus" />
            </template>
            创建预测任务
          </NButton>
        </template>
      </TableHeaderOperation>

      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="1200"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
    </NCard>

    <!-- 操作抽屉 -->
    <HealthPredictionOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @submitted="getDataByPage"
    />

    <!-- 模型管理器弹窗 -->
    <PredictionModelManager v-model:visible="modelManagerVisible" @model-updated="getData" />

    <!-- 预测结果查看器 -->
    <PredictionResultViewer v-model:visible="resultViewerVisible" :task-data="selectedTaskResult" />
    
    <!-- AI预测管理弹窗 -->
    <NModal v-model:show="aiPredictionVisible" preset="card" style="width: 90vw; max-width: 1200px;" title="AI健康预测管理">
      <AiModelsManagement />
    </NModal>
  </div>
</template>

<style scoped>
.card-wrapper :deep(.n-card__content) {
  @apply flex-1-hidden;
}

.text-primary {
  color: var(--primary-color);
}

.text-success {
  color: var(--success-color);
}

.text-info {
  color: var(--info-color);
}

.text-warning {
  color: var(--warning-color);
}
</style>
