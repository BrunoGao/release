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
import HealthRecommendationSearch from './modules/health-recommendation-search.vue';
import HealthRecommendationOperateDrawer from './modules/health-recommendation-operate-drawer.vue';
import RecommendationTemplateManager from './modules/recommendation-template-manager.vue';
import RecommendationAnalytics from './modules/recommendation-analytics.vue';

defineOptions({
  name: 'HealthRecommendationPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');
const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.RecommendationTask | null> = ref(null);
const templateManagerVisible = ref(false);
const analyticsVisible = ref(false);

// 模拟 API 调用函数
const fetchGetRecommendationList = async (params: any) => {
  await new Promise(resolve => setTimeout(resolve, 1000));

  const mockRecommendations = [
    {
      id: '1',
      userName: '张三',
      userDepartment: '技术部',
      recommendationType: 'lifestyle',
      priority: 'high',
      title: '改善睡眠质量建议',
      content: '建议您调整作息时间，每天保证7-8小时的睡眠，睡前1小时避免使用电子设备。',
      healthScore: 72,
      riskFactors: ['睡眠不足', '压力过大'],
      status: 'pending',
      createdAt: '2024-01-21 14:30:00',
      scheduledAt: '2024-01-22 09:00:00',
      readAt: null,
      feedback: null,
      effectivenesScore: null,
      aiGenerated: true,
      templateId: 'T001'
    },
    {
      id: '2',
      userName: '李四',
      userDepartment: '销售部',
      recommendationType: 'exercise',
      priority: 'medium',
      title: '心血管健康运动计划',
      content: '建议每周进行3-4次中等强度有氧运动，如快走、游泳或骑行，每次30-45分钟。',
      healthScore: 65,
      riskFactors: ['心率偏高', '运动不足'],
      status: 'sent',
      createdAt: '2024-01-20 16:45:00',
      scheduledAt: '2024-01-21 08:00:00',
      readAt: '2024-01-21 10:30:00',
      feedback: 'helpful',
      effectivenesScore: 4,
      aiGenerated: true,
      templateId: 'T002'
    },
    {
      id: '3',
      userName: '王五',
      userDepartment: '市场部',
      recommendationType: 'nutrition',
      priority: 'low',
      title: '血压管理饮食建议',
      content: '建议减少钠盐摄入，增加富含钾的食物如香蕉、菠菜等，保持均衡饮食。',
      healthScore: 78,
      riskFactors: ['血压偏高'],
      status: 'completed',
      createdAt: '2024-01-19 11:20:00',
      scheduledAt: '2024-01-20 07:00:00',
      readAt: '2024-01-20 08:15:00',
      feedback: 'very_helpful',
      effectivenesScore: 5,
      aiGenerated: false,
      templateId: null
    }
  ];

  return {
    error: null,
    data: {
      records: mockRecommendations,
      total: mockRecommendations.length,
      page: params.page || 1,
      pageSize: params.pageSize || 20
    }
  };
};

const fetchDeleteRecommendation = async (ids: string[]) => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return { error: null, data: { success: true } };
};

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetRecommendationList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    status: null,
    type: null,
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
      key: 'userName',
      title: '目标用户',
      align: 'center',
      minWidth: 100,
      render: row => (
        <div>
          <div class="font-medium">{row.userName}</div>
          <div class="text-xs text-gray-500">{row.userDepartment}</div>
        </div>
      )
    },
    {
      key: 'title',
      title: '建议标题',
      align: 'left',
      minWidth: 200,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'recommendationType',
      title: '建议类型',
      align: 'center',
      width: 120,
      render: row => {
        const typeMap = {
          lifestyle: { type: 'info', text: '生活方式' },
          exercise: { type: 'success', text: '运动健身' },
          nutrition: { type: 'warning', text: '营养饮食' },
          medical: { type: 'error', text: '医疗建议' },
          mental: { type: 'primary', text: '心理健康' }
        } as const;
        const typeInfo = typeMap[row.recommendationType as keyof typeof typeMap];
        return h(NTag, { type: typeInfo.type, size: 'small' }, () => typeInfo.text);
      }
    },
    {
      key: 'priority',
      title: '优先级',
      align: 'center',
      width: 100,
      render: row => {
        const priorityMap = {
          high: { type: 'error', text: '高' },
          medium: { type: 'warning', text: '中' },
          low: { type: 'success', text: '低' }
        } as const;
        const priority = priorityMap[row.priority as keyof typeof priorityMap];
        return h(NTag, { type: priority.type, size: 'small' }, () => priority.text);
      }
    },
    {
      key: 'status',
      title: '状态',
      align: 'center',
      width: 100,
      render: row => {
        const statusMap = {
          pending: { type: 'warning', text: '待发送' },
          sent: { type: 'info', text: '已发送' },
          read: { type: 'primary', text: '已查看' },
          completed: { type: 'success', text: '已完成' },
          rejected: { type: 'error', text: '已拒绝' }
        } as const;
        const status = statusMap[row.status as keyof typeof statusMap];
        return h(NTag, { type: status.type, size: 'small' }, () => status.text);
      }
    },
    {
      key: 'healthScore',
      title: '健康评分',
      align: 'center',
      width: 100,
      render: row => (
        <div class="flex items-center justify-center">
          <span class={`font-medium ${row.healthScore >= 80 ? 'text-green-600' : row.healthScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
            {row.healthScore}
          </span>
        </div>
      )
    },
    {
      key: 'aiGenerated',
      title: '生成方式',
      align: 'center',
      width: 100,
      render: row => (
        <NTag type={row.aiGenerated ? 'info' : 'default'} size="small">
          {row.aiGenerated ? 'AI生成' : '手动创建'}
        </NTag>
      )
    },
    {
      key: 'effectivenesScore',
      title: '有效性评分',
      align: 'center',
      width: 120,
      render: row => {
        if (row.effectivenesScore === null) {
          return '-';
        }
        const score = row.effectivenesScore;
        return (
          <div class="flex items-center justify-center">
            <span class={`font-medium ${score >= 4 ? 'text-green-600' : score >= 3 ? 'text-yellow-600' : 'text-red-600'}`}>{score}/5</span>
          </div>
        );
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
      width: 280,
      minWidth: 280,
      render: row => (
        <NSpace size="small">
          <NButton type="info" quaternary size="small" onClick={() => viewAnalytics(row)}>
            查看详情
          </NButton>
          {row.status === 'pending' && hasAuth('health:recommendation:send') && (
            <NButton type="primary" quaternary size="small" onClick={() => sendRecommendation(row)}>
              发送
            </NButton>
          )}
          {hasAuth('health:recommendation:edit') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('health:recommendation:delete') && (
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

function edit(item: Api.Health.RecommendationTask) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

function viewAnalytics(item: Api.Health.RecommendationTask) {
  editingData.value = item;
  analyticsVisible.value = true;
}

function openTemplateManager() {
  templateManagerVisible.value = true;
}

async function sendRecommendation(item: Api.Health.RecommendationTask) {
  // 模拟发送操作
  await new Promise(resolve => setTimeout(resolve, 1000));

  const index = data.value.findIndex(d => d.id === item.id);
  if (index > -1) {
    data.value[index].status = 'sent';
    data.value[index].scheduledAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
  }

  window.$message?.success('健康建议发送成功');
}

async function handleDelete(id: string) {
  const { error, data: result } = await fetchDeleteRecommendation([id]);
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  const { error, data: result } = await fetchDeleteRecommendation(checkedRowKeys.value);
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
const recommendationStats = computed(() => {
  const stats = {
    total: data.value.length,
    pending: 0,
    sent: 0,
    completed: 0,
    avgEffectiveness: 0
  };

  let totalEffectiveness = 0;
  let completedCount = 0;

  data.value.forEach(item => {
    if (item.status === 'pending') {
      stats.pending++;
    } else if (item.status === 'sent' || item.status === 'read') {
      stats.sent++;
    } else if (item.status === 'completed') {
      stats.completed++;
      if (item.effectivenesScore) {
        totalEffectiveness += item.effectivenesScore;
        completedCount++;
      }
    }
  });

  stats.avgEffectiveness = completedCount > 0 ? totalEffectiveness / completedCount : 0;
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
            <div class="text-sm text-gray-600">总建议数</div>
            <div class="text-2xl text-primary font-bold">{{ recommendationStats.total }}</div>
          </div>
          <div class="text-3xl text-primary opacity-20">💡</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">待发送</div>
            <div class="text-2xl text-warning font-bold">{{ recommendationStats.pending }}</div>
          </div>
          <div class="text-3xl text-warning opacity-20">⏳</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">已完成</div>
            <div class="text-2xl text-success font-bold">{{ recommendationStats.completed }}</div>
          </div>
          <div class="text-3xl text-success opacity-20">✅</div>
        </div>
      </NCard>

      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">平均有效性</div>
            <div class="text-2xl text-info font-bold">{{ recommendationStats.avgEffectiveness.toFixed(1) }}/5</div>
          </div>
          <div class="text-3xl text-info opacity-20">📊</div>
        </div>
      </NCard>
    </div>

    <!-- 搜索组件 -->
    <HealthRecommendationSearch
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
          <span class="text-lg font-semibold">健康建议管理</span>
          <NSpace>
            <NButton type="info" @click="openTemplateManager">
              <template #icon>
                <div class="i-mdi:file-document-multiple" />
              </template>
              模板管理
            </NButton>
          </NSpace>
        </div>
      </template>

      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="health:recommendation:add"
        delete-auth="health:recommendation:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #default>
          <NButton type="primary" @click="handleAdd">
            <template #icon>
              <div class="i-mdi:plus" />
            </template>
            创建健康建议
          </NButton>
        </template>
      </TableHeaderOperation>

      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="1400"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
    </NCard>

    <!-- 操作抽屉 -->
    <HealthRecommendationOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @submitted="getDataByPage"
    />

    <!-- 模板管理器弹窗 -->
    <RecommendationTemplateManager v-model:visible="templateManagerVisible" @template-updated="getData" />

    <!-- 分析详情弹窗 -->
    <RecommendationAnalytics v-model:visible="analyticsVisible" :recommendation-data="editingData" />
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
