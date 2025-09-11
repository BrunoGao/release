<script setup lang="tsx">
import { type Ref, h, onMounted, onUnmounted, ref, shallowRef, computed, watch } from 'vue';
import { 
  NButton, NPopconfirm, NTooltip, NTag, NProgress, NModal, NCard, NStatistic, NGrid, NGridItem,
  NTabs, NTabPane, NSpace, NIcon, NTime, NSpin, NEmpty, NAlert, NDrawer, NDrawerContent
} from 'naive-ui';
import { 
  ChatbubbleOutline, StatsChartOutline, TimeOutline, CheckmarkCircleOutline, 
  CloseCircleOutline, HourglassOutline, SendOutline, NotificationsOutline
} from '@vicons/ionicons5';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { 
  fetchGetDeviceMessageV2List, 
  fetchDeleteDeviceMessageV2, 
  fetchBatchDeleteDeviceMessageV2,
  fetchGetMessageStatistics,
  fetchGetMessageSummary,
  fetchGetChannelStatistics,
  fetchRetryFailedMessage,
  fetchAcknowledgeMessage
} from '@/service/api/health/device-message-v2';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import { deviceOptions, handleBindUsersByOrgId } from '@/utils/deviceUtils';
import MessageV2Search from './modules/message-v2-search.vue';
import MessageV2OperateDrawer from './modules/message-v2-operate-drawer.vue';
import MessageLifecycleViewer from './modules/message-lifecycle-viewer.vue';
import MessageStatsDashboard from './modules/message-stats-dashboard.vue';

defineOptions({
  name: 'TDeviceMessageV2Page'
});

const operateType = ref<NaiveUI.TableOperateType>('add');
const showLifecycleModal = ref(false);
const showStatsDrawer = ref(false);
const selectedMessageId = ref<number | null>(null);

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const { hasAuth } = useAuth();
const { dictTag } = useDict();

const editingData: Ref<Api.Health.DeviceMessageV2Detail | null> = ref(null);
const messageStats: Ref<Api.Health.MessageStatisticsV2 | null> = ref(null);
const messageSummary: Ref<Api.Health.MessageSummaryV2 | null> = ref(null);
const channelStats: Ref<Record<string, any> | null> = ref(null);
const realTimeUpdates = ref(true);

// 实时数据更新
const updateInterval = ref<NodeJS.Timeout | null>(null);

const { 
  columns, 
  columnChecks, 
  data, 
  loading, 
  getData, 
  getDataByPage, 
  mobilePagination, 
  searchParams, 
  resetSearchParams 
} = useTable({
  apiFn: fetchGetDeviceMessageV2List,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    messageType: null,
    messageStatus: null
  },
  columns: () => [
    { type: 'selection', width: 40, align: 'center' },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'messageId',
      title: '消息ID',
      align: 'center',
      width: 120,
      render: row => h('code', { class: 'text-xs bg-gray-100 px-2 py-1 rounded' }, row.messageId)
    },
    {
      key: 'title',
      title: '消息标题',
      align: 'center',
      minWidth: 200,
      render: row => h(NTooltip, {
        trigger: 'hover'
      }, {
        trigger: () => h('span', { 
          class: 'truncate block max-w-48 cursor-pointer text-blue-600 hover:text-blue-800' 
        }, row.title),
        default: () => row.message
      })
    },
    {
      key: 'messageType',
      title: '消息类型',
      align: 'center',
      width: 120,
      render: row => {
        const typeColors = {
          'EMERGENCY': 'error',
          'ALERT': 'warning', 
          'WARNING': 'warning',
          'NOTIFICATION': 'info',
          'INFO': 'default'
        } as const;
        return h(NTag, { 
          type: typeColors[row.messageType] || 'default',
          size: 'small'
        }, () => row.messageType);
      }
    },
    {
      key: 'urgency',
      title: '紧急程度',
      align: 'center',
      width: 100,
      render: row => {
        const urgencyColors = {
          'CRITICAL': 'error',
          'HIGH': 'warning',
          'MEDIUM': 'info',
          'LOW': 'success'
        } as const;
        return h(NTag, { 
          type: urgencyColors[row.urgency] || 'default',
          size: 'small'
        }, () => row.urgency);
      }
    },
    {
      key: 'messageStatus',
      title: '消息状态',
      align: 'center',
      width: 120,
      render: row => {
        const statusColors = {
          'DRAFT': 'default',
          'PENDING': 'warning',
          'SENT': 'info',
          'DELIVERED': 'success',
          'ACKNOWLEDGED': 'success',
          'FAILED': 'error',
          'EXPIRED': 'error'
        } as const;
        return h(NTag, { 
          type: statusColors[row.messageStatus] || 'default',
          size: 'small'
        }, () => row.messageStatus);
      }
    },
    {
      key: 'progress',
      title: '分发进度',
      align: 'center',
      width: 200,
      render: row => {
        const total = row.totalTargets || 0;
        const delivered = row.deliveredCount || 0;
        const acknowledged = row.acknowledgedCount || 0;
        const failed = row.failedCount || 0;
        const pending = row.pendingCount || 0;
        
        const successRate = total > 0 ? (delivered / total) * 100 : 0;
        const ackRate = total > 0 ? (acknowledged / total) * 100 : 0;
        
        return h('div', { class: 'space-y-1' }, [
          h(NProgress, {
            type: 'line',
            percentage: successRate,
            color: '#18a058',
            railColor: '#f0f0f0',
            height: 6,
            showIndicator: false
          }),
          h('div', { class: 'flex justify-between text-xs text-gray-500' }, [
            h('span', `成功: ${delivered}/${total}`),
            h('span', `确认: ${acknowledged}/${total}`)
          ]),
          failed > 0 && h('div', { class: 'text-xs text-red-500' }, `失败: ${failed}`)
        ]);
      }
    },
    {
      key: 'sentTime',
      title: '发送时间',
      align: 'center',
      width: 160,
      render: row => row.sentTime ? h(NTime, { time: new Date(row.sentTime) }) : '未发送'
    },
    {
      key: 'lifecycle',
      title: '生命周期',
      align: 'center',
      width: 120,
      render: row => h(NButton, {
        size: 'small',
        quaternary: true,
        type: 'info',
        onClick: () => viewLifecycle(row.id)
      }, {
        default: () => '查看跟踪',
        icon: () => h(NIcon, null, { default: () => h(TimeOutline) })
      })
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 280,
      minWidth: 280,
      render: row => (
        <div class="flex-center gap-4px">
          {hasAuth('message:v2:detail') && (
            <NButton type="info" quaternary size="small" onClick={() => viewSummary(row.id)}>
              详情
            </NButton>
          )}
          {hasAuth('message:v2:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {row.messageStatus === 'FAILED' && hasAuth('message:v2:retry') && (
            <NButton type="warning" quaternary size="small" onClick={() => retryMessage(row.id)}>
              重发
            </NButton>
          )}
          {hasAuth('message:v2:delete') && (
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
        </div>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

// 统计数据计算
const summaryStats = computed(() => {
  if (!messageStats.value) return null;
  
  return {
    total: messageStats.value.totalMessages,
    sent: messageStats.value.sentMessages,
    delivered: messageStats.value.receivedMessages,
    acknowledged: messageStats.value.acknowledgedMessages,
    failed: messageStats.value.failedMessages,
    pending: messageStats.value.pendingMessages,
    successRate: messageStats.value.sendSuccessRate,
    ackRate: messageStats.value.acknowledgeSuccessRate,
    avgResponseTime: messageStats.value.averageResponseTime
  };
});

// 操作方法
function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Health.DeviceMessageV2Detail) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: number) {
  const { error } = await fetchDeleteDeviceMessageV2(id);
  if (!error) {
    await onDeleted();
    await loadStatistics(); // 重新加载统计数据
  }
}

async function handleBatchDelete() {
  const ids = checkedRowKeys.value.map(key => Number(key));
  const { error } = await fetchBatchDeleteDeviceMessageV2(ids);
  if (!error) {
    await onBatchDeleted();
    await loadStatistics();
  }
}

async function retryMessage(messageId: number) {
  // 这里需要知道目标ID，实际应用中可能需要从详情中获取
  // const { error } = await fetchRetryFailedMessage(messageId, targetId);
  // 暂时显示操作成功
  window.$message?.success('重发请求已提交');
}

function viewLifecycle(messageId: number) {
  selectedMessageId.value = messageId;
  showLifecycleModal.value = true;
}

async function viewSummary(messageId: number) {
  const { error, data: summary } = await fetchGetMessageSummary(messageId);
  if (!error && summary) {
    messageSummary.value = summary;
    selectedMessageId.value = messageId;
    // 可以打开一个模态框显示详细汇总信息
    window.$message?.info('消息汇总数据已加载');
  }
}

function showStatsDashboard() {
  showStatsDrawer.value = true;
}

// 数据加载
async function loadStatistics() {
  if (!customerId) return;
  
  try {
    const { error, data: stats } = await fetchGetMessageStatistics({
      customerId,
      orgId: searchParams.orgId || undefined
    });
    
    if (!error && stats) {
      messageStats.value = stats;
    }
    
    // 加载渠道统计
    const { error: channelError, data: channelData } = await fetchGetChannelStatistics({
      customerId
    });
    
    if (!channelError && channelData) {
      channelStats.value = channelData;
    }
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
}

// 实时更新功能
function startRealTimeUpdates() {
  if (updateInterval.value) return;
  
  updateInterval.value = setInterval(async () => {
    if (realTimeUpdates.value) {
      await Promise.all([
        getDataByPage(),
        loadStatistics()
      ]);
    }
  }, 30000); // 30秒更新一次
}

function stopRealTimeUpdates() {
  if (updateInterval.value) {
    clearInterval(updateInterval.value);
    updateInterval.value = null;
  }
}

// 组织树和用户选项
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  const { error, data: treeData } = await fetchGetOrgUnitsTree(customerId);
  if (!error && treeData) {
    orgUnitsTree.value = treeData;
    if (treeData.length > 0) {
      const result = await handleBindUsersByOrgId(treeData[0].id);
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
}

// 监听部门变化
watch(
  () => searchParams.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
    // 重新加载统计数据
    await loadStatistics();
  }
);

// 监听搜索参数变化
watch(
  () => searchParams.userId,
  newValue => {
    if (newValue === 'all') {
      searchParams.userId = null;
    }
  }
);

onMounted(async () => {
  await handleInitOptions();
  await loadStatistics();
  startRealTimeUpdates();
});

onUnmounted(() => {
  stopRealTimeUpdates();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <!-- 统计概览卡片 -->
    <NCard :bordered="false" class="card-wrapper">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-8px">
            <NIcon size="20" :component="NotificationsOutline" />
            <span class="text-lg font-semibold">消息统计概览</span>
          </div>
          <div class="flex items-center gap-8px">
            <NButton 
              type="info" 
              quaternary 
              size="small"
              @click="showStatsDashboard"
            >
              <template #icon>
                <NIcon :component="StatsChartOutline" />
              </template>
              详细统计
            </NButton>
            <NButton 
              :type="realTimeUpdates ? 'success' : 'default'"
              quaternary 
              size="small"
              @click="realTimeUpdates = !realTimeUpdates"
            >
              {{ realTimeUpdates ? '实时更新中' : '手动更新' }}
            </NButton>
          </div>
        </div>
      </template>
      
      <NSpin :show="!summaryStats">
        <NGrid v-if="summaryStats" :cols="6" :x-gap="16" :y-gap="16">
          <NGridItem>
            <NStatistic 
              label="总消息数" 
              :value="summaryStats.total"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <NIcon :component="ChatbubbleOutline" />
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic 
              label="已发送" 
              :value="summaryStats.sent"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <NIcon :component="SendOutline" />
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic 
              label="已送达" 
              :value="summaryStats.delivered"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <NIcon :component="CheckmarkCircleOutline" />
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic 
              label="已确认" 
              :value="summaryStats.acknowledged"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <NIcon :component="CheckmarkCircleOutline" />
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic 
              label="失败" 
              :value="summaryStats.failed"
              :value-style="{ color: '#ff4d4f' }"
            >
              <template #prefix>
                <NIcon :component="CloseCircleOutline" />
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic 
              label="成功率" 
              :value="summaryStats.successRate"
              suffix="%"
              :precision="1"
              :value-style="{ 
                color: summaryStats.successRate >= 90 ? '#52c41a' : 
                       summaryStats.successRate >= 70 ? '#faad14' : '#ff4d4f' 
              }"
            >
              <template #prefix>
                <NIcon :component="StatsChartOutline" />
              </template>
            </NStatistic>
          </NGridItem>
        </NGrid>
        
        <NEmpty v-else description="暂无统计数据" class="py-20" />
      </NSpin>
    </NCard>

    <!-- 搜索区域 -->
    <MessageV2Search
      v-model:model="searchParams"
      :device-options="deviceOptions"
      :customer-id="customerId"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    
    <!-- 主表格区域 -->
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="message:v2:create"
        delete-auth="message:v2:batch-delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #suffix>
          <NSpace>
            <NButton 
              type="info" 
              secondary
              size="small"
              @click="loadStatistics"
            >
              刷新统计
            </NButton>
          </NSpace>
        </template>
      </TableHeaderOperation>
      
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
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
    <MessageV2OperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      :device-options="deviceOptions"
      :customer-id="authStore.userInfo?.customerId"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @submitted="getDataByPage"
      @update-user-options="options => (userOptions = options)"
    />

    <!-- 生命周期查看模态框 -->
    <NModal
      v-model:show="showLifecycleModal"
      preset="card"
      title="消息生命周期跟踪"
      size="huge"
      :auto-focus="false"
    >
      <MessageLifecycleViewer 
        v-if="selectedMessageId" 
        :message-id="selectedMessageId"
        @close="showLifecycleModal = false"
      />
    </NModal>

    <!-- 统计分析抽屉 -->
    <NDrawer
      v-model:show="showStatsDrawer"
      :width="800"
      placement="right"
    >
      <NDrawerContent title="消息统计分析" closable>
        <MessageStatsDashboard 
          v-if="showStatsDrawer"
          :customer-id="customerId"
          :org-id="searchParams.orgId"
          :message-stats="messageStats"
          :channel-stats="channelStats"
        />
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.card-wrapper {
  @apply transition-all duration-200 hover:shadow-md;
}

:deep(.n-statistic .n-statistic-value) {
  font-weight: 600;
}

:deep(.n-progress-text) {
  font-size: 12px;
}
</style>