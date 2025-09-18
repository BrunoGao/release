<script setup lang="tsx">
import { NButton, NCard, NPopconfirm, NStatistic, NTabPane, NTabs, NTooltip } from 'naive-ui';
import { type Ref, computed, h, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteDeviceMessage, fetchGetDeviceMessageList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import { deviceOptions, handleBindUsersByOrgId } from '@/utils/deviceUtils';
import DeviceMessageSearch from './modules/device-message-search.vue';
import DeviceMessageOperateDrawer from './modules/device-message-operate-drawer.vue';
defineOptions({
  name: 'TDeviceMessagePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const { hasAuth } = useAuth();

const { dictTag } = useDict();

// 消息类型中英文映射和样式
const messageTypeMap = {
  NOTIFICATION: '通知',
  ALERT: '告警',
  WARNING: '警告',
  INFO: '信息',
  EMERGENCY: '紧急',
  JOB: '作业指引',
  TASK: '任务管理'
};

// 发送者类型中英文映射
const senderTypeMap = {
  SYSTEM: '系统',
  ADMIN: '管理员',
  USER: '用户',
  DEVICE: '设备',
  SERVICE: '服务',
  AUTO: '自动'
};

// 消息状态中英文映射
const messageStatusMap = {
  DRAFT: '草稿',
  PENDING: '待发送',
  SENT: '已发送',
  DELIVERED: '已送达',
  ACKNOWLEDGED: '已确认',
  FAILED: '发送失败',
  EXPIRED: '已过期'
};

// 获取消息类型标签颜色
const getMessageTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    NOTIFICATION: '#1890ff',
    ALERT: '#ff4d4f',
    WARNING: '#faad14',
    INFO: '#52c41a',
    EMERGENCY: '#f5222d',
    JOB: '#13c2c2',
    TASK: '#722ed1'
  };
  return colorMap[type] || '#666';
};

// 获取发送者类型标签颜色
const getSenderTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    SYSTEM: '#1890ff',
    ADMIN: '#722ed1',
    USER: '#52c41a',
    DEVICE: '#13c2c2',
    SERVICE: '#faad14',
    AUTO: '#666'
  };
  return colorMap[type] || '#666';
};

// 获取消息状态标签颜色
const getMessageStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    DRAFT: '#666',
    PENDING: '#faad14',
    SENT: '#1890ff',
    DELIVERED: '#52c41a',
    ACKNOWLEDGED: '#52c41a',
    FAILED: '#ff4d4f',
    EXPIRED: '#666'
  };
  return colorMap[status] || '#666';
};

// 增强的标签函数，支持消息类型、发送者类型、消息状态中文映射
const enhancedMessageTag = (code: string, value: string | null) => {
  if (!value) return null;

  if (code === 'message_type') {
    const chineseValue = messageTypeMap[value as keyof typeof messageTypeMap] || value;
    const color = getMessageTypeColor(value);
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  if (code === 'sender_type') {
    const chineseValue = senderTypeMap[value as keyof typeof senderTypeMap] || value;
    const color = getSenderTypeColor(value);
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  if (code === 'message_status') {
    const chineseValue = messageStatusMap[value as keyof typeof messageStatusMap] || value;
    const color = getMessageStatusColor(value);
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  // 否则使用原来的字典标签
  return dictTag(code, value);
};

const editingData: Ref<Api.Health.DeviceMessage | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetDeviceMessageList,
  apiParams: {
    page: 1,
    pageSize: 20,
    orgId: customerId,
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
      key: 'orgName',
      title: $t('page.health.device.info.orgName'),
      align: 'center',
      minWidth: 120,
      render: row => row.orgName || '-'
    },
    {
      key: 'userName',
      title: $t('page.health.data.info.username'),
      align: 'center',
      minWidth: 120,
      render: row => row.userName || (row.receiverType === 'GROUP' ? '群组消息' : row.userId || '-')
    },
    {
      key: 'targetCount',
      title: '目标数量',
      align: 'center',
      width: 80,
      render: row => row.targetCount || 1
    },
    {
      key: 'respondedNumber',
      title: '响应数量',
      align: 'center',
      width: 80,
      render: row => row.respondedNumber || 0
    },
    {
      key: 'message',
      title: $t('page.health.device.message.message'),
      align: 'center',
      width: 300
    },
    {
      key: 'messageType',
      title: $t('page.health.device.message.messageType'),
      align: 'center',
      minWidth: 100,
      render: row => {
        // 优先使用中文名称，如果为空则使用原字段，再为空则使用默认值
        const displayValue = row.messageTypeName || row.messageType || 'NOTIFICATION';
        return enhancedMessageTag('message_type', displayValue);
      }
    },
    {
      key: 'senderType',
      title: '发送者类型',
      align: 'center',
      minWidth: 100,
      render: row => {
        // 优先使用中文名称，如果为空则使用原字段，再为空则使用默认值
        const displayValue = row.senderTypeName || row.senderType || 'SYSTEM';
        return enhancedMessageTag('sender_type', displayValue);
      }
    },
    {
      key: 'messageStatus',
      title: $t('page.health.device.message.messageStatus'),
      align: 'center',
      minWidth: 100,
      render: row => {
        const rawStatus = row.messageStatus;
        // 使用增强标签获取状态标签
        const statusTag = enhancedMessageTag('message_status', rawStatus);
        const statusCount = `[${row.respondedNumber || 0}/${row.targetCount || 1}]`;

        // 创建美化的悬浮提示内容
        const nonRespondedUsers = row.respondedDetail?.nonRespondedUsers || [];
        const hasUsers = nonRespondedUsers.length > 0;

        const tooltipContent = h(
          'div',
          {
            class: 'max-w-80 p-3 bg-white shadow-lg rounded-lg border border-gray-100'
          },
          [
            // 标题
            h(
              'div',
              {
                class: 'flex items-center gap-2 mb-3 pb-2 border-b border-gray-100'
              },
              [
                h('div', {
                  class: `w-2 h-2 rounded-full ${hasUsers ? 'bg-orange-400' : 'bg-green-400'}`
                }),
                h(
                  'span',
                  {
                    class: 'font-semibold text-gray-800 text-sm'
                  },
                  hasUsers ? '未响应用户列表' : '响应状态'
                )
              ]
            ),

            // 内容区域
            hasUsers
              ? h('div', { class: 'space-y-2 max-h-60 overflow-y-auto' }, [
                  ...nonRespondedUsers.map(user =>
                    h(
                      'div',
                      {
                        class: 'flex items-center justify-between p-2 bg-orange-50 rounded-md border-l-3 border-orange-400'
                      },
                      [
                        h('div', { class: 'flex flex-col' }, [
                          h('span', { class: 'text-sm font-medium text-gray-800' }, user.userName),
                          h('span', { class: 'text-xs text-gray-500' }, user.departmentName)
                        ]),
                        h('div', {
                          class: 'w-2 h-2 rounded-full bg-orange-400'
                        })
                      ]
                    )
                  ),
                  // 如果用户太多，显示查看更多提示
                  nonRespondedUsers.length > 5 &&
                    h(
                      'div',
                      {
                        class: 'text-xs text-gray-400 text-center pt-2 border-t border-gray-100'
                      },
                      '向上滚动查看更多用户'
                    )
                ])
              : h(
                  'div',
                  {
                    class: 'flex items-center gap-2 p-2 bg-green-50 rounded-md border-l-3 border-green-400'
                  },
                  [
                    h(
                      'svg',
                      {
                        class: 'w-4 h-4 text-green-500',
                        fill: 'currentColor',
                        viewBox: '0 0 20 20'
                      },
                      [
                        h('path', {
                          'fill-rule': 'evenodd',
                          d: 'M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z',
                          'clip-rule': 'evenodd'
                        })
                      ]
                    ),
                    h('span', { class: 'text-sm text-green-700' }, '所有用户均已响应')
                  ]
                )
          ]
        );

        return h(
          NTooltip,
          {
            trigger: 'hover',
            placement: 'top',
            showArrow: false,
            style: { maxWidth: 'none' },
            contentStyle: {
              padding: '0',
              background: 'transparent',
              border: 'none',
              boxShadow: 'none'
            }
          },
          {
            trigger: () =>
              h(
                'div',
                {
                  class: 'cursor-pointer flex items-center gap-2'
                },
                [statusTag, h('span', { class: 'text-xs text-gray-500' }, statusCount)]
              ),
            default: () => tooltipContent
          }
        );
      }
    },
    {
      key: 'sentTime',
      title: $t('page.health.device.message.sentTime'),
      align: 'center',
      minWidth: 50,
      render: row => convertToBeijingTime(row.sentTime)
    },
    {
      key: 'receivedTime',
      title: $t('page.health.device.message.receivedTime'),
      align: 'center',
      minWidth: 50,
      render: row => (row.receivedTime ? convertToBeijingTime(row.receivedTime) : '未接收') // 空值显示未接收#
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:device:message:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:device:message:delete') && (
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

function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Health.DeviceMessage) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteDeviceMessage(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}
// 监听 searchParams 变化，处理 userId 为 'all' 的情况
watch(
  () => searchParams.userId,
  newValue => {
    if (newValue === 'all') {
      searchParams.userId = null; // 当 userId 为 'all' 时，设置为 null
    }
  }
);
async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteDeviceMessage(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
      // 初始化时获取第一个部门的员工列表
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

// ==================== 统计数据计算 ====================
const statistics = computed(() => {
  if (!data.value || data.value.length === 0) {
    return {
      total: 0,
      byType: {},
      byStatus: {},
      byUrgency: {},
      responseRate: 0,
      averageResponseTime: 0
    };
  }

  const stats = {
    total: data.value.length,
    byType: {} as Record<string, number>,
    byStatus: {} as Record<string, number>,
    byUrgency: {} as Record<string, number>,
    responseRate: 0,
    averageResponseTime: 0
  };

  let totalResponseTime = 0;
  let responseCount = 0;

  data.value.forEach(item => {
    // 按类型统计（翻译为中文）
    const rawType = item.messageTypeName || item.messageType || 'UNKNOWN';
    const typeMap = {
      NOTIFICATION: '通知消息',
      ALERT: '警报消息',
      WARNING: '警告消息',
      INFO: '信息消息',
      EMERGENCY: '紧急消息',
      JOB: '任务消息',
      TASK: '工作消息',
      UNKNOWN: '未知类型'
    };
    const type = typeMap[rawType] || rawType;
    stats.byType[type] = (stats.byType[type] || 0) + 1;

    // 按状态统计（翻译为中文）
    const rawStatus = item.messageStatusName || item.messageStatus || 'UNKNOWN';
    const statusMap = {
      DRAFT: '草稿',
      PENDING: '待发送',
      SENT: '已发送',
      DELIVERED: '已送达',
      ACKNOWLEDGED: '已确认',
      FAILED: '发送失败',
      EXPIRED: '已过期',
      UNKNOWN: '未知状态'
    };
    const status = statusMap[rawStatus] || rawStatus;
    stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

    // 按紧急程度统计（翻译为中文）
    const rawUrgency = item.urgencyName || item.urgency || 'MEDIUM';
    const urgencyMap = {
      CRITICAL: '非常紧急',
      HIGH: '高级',
      MEDIUM: '中级',
      LOW: '低级',
      UNKNOWN: '未知级别'
    };
    const urgency = urgencyMap[rawUrgency] || rawUrgency;
    stats.byUrgency[urgency] = (stats.byUrgency[urgency] || 0) + 1;

    // 响应时间计算
    if (item.sentTime && item.receivedTime) {
      const responseTime = new Date(item.receivedTime).getTime() - new Date(item.sentTime).getTime();
      if (responseTime > 0) {
        totalResponseTime += responseTime;
        responseCount++;
      }
    }
  });

  // 计算响应率（已响应/总数）
  const acknowledgedCount = stats.byStatus['已确认'] || 0;
  const deliveredCount = stats.byStatus['已送达'] || 0;
  stats.responseRate = Math.round(((acknowledgedCount + deliveredCount) / stats.total) * 100);

  // 计算平均响应时间（分钟）
  stats.averageResponseTime = responseCount > 0 ? Math.round(totalResponseTime / responseCount / 60000) : 0;

  return stats;
});

// 消息类型颜色映射（使用中文名称）
const typeColors = {
  通知消息: 'rgba(24, 144, 255, 0.8)', // 蓝色
  警报消息: 'rgba(245, 34, 45, 0.8)', // 红色
  警告消息: 'rgba(250, 173, 20, 0.8)', // 橙色
  信息消息: 'rgba(82, 196, 26, 0.8)', // 绿色
  紧急消息: 'rgba(114, 46, 209, 0.8)', // 紫色
  任务消息: 'rgba(19, 194, 194, 0.8)', // 青色
  工作消息: 'rgba(135, 208, 104, 0.8)', // 浅绿色
  未知类型: 'rgba(140, 140, 140, 0.8)' // 灰色
};

// 状态颜色映射（使用中文名称）
const statusColors = {
  草稿: 'rgba(217, 217, 217, 0.8)', // 灰色
  待发送: 'rgba(250, 173, 20, 0.8)', // 橙色
  已发送: 'rgba(24, 144, 255, 0.8)', // 蓝色
  已送达: 'rgba(82, 196, 26, 0.8)', // 绿色
  已确认: 'rgba(82, 196, 26, 0.8)', // 绿色
  发送失败: 'rgba(245, 34, 45, 0.8)', // 红色
  已过期: 'rgba(140, 140, 140, 0.8)', // 灰色
  未知状态: 'rgba(140, 140, 140, 0.8)' // 灰色
};

onMounted(() => {
  handleInitOptions();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <DeviceMessageSearch
      v-model:model="searchParams"
      :device-options="deviceOptions"
      :customer-id="customerId"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />

    <!-- 统计概览卡片 -->
    <NCard :bordered="false" class="card-wrapper">
      <template #header>
        <div class="flex items-center gap-2">
          <icon-fluent:data-pie-24-regular class="text-lg text-primary" />
          <span class="font-medium">消息统计概览</span>
        </div>
      </template>

      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <!-- 总消息数 -->
        <div class="border border-blue-200 rounded-lg from-blue-50 to-blue-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-blue-600 font-bold">{{ statistics.total }}</div>
          <div class="mt-1 text-sm text-blue-500">总消息数</div>
        </div>

        <!-- 响应率 -->
        <div class="border border-green-200 rounded-lg from-green-50 to-green-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-green-600 font-bold">{{ statistics.responseRate }}%</div>
          <div class="mt-1 text-sm text-green-500">响应率</div>
        </div>

        <!-- 平均响应时间 -->
        <div class="border border-orange-200 rounded-lg from-orange-50 to-orange-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-orange-600 font-bold">{{ statistics.averageResponseTime }}</div>
          <div class="mt-1 text-sm text-orange-500">平均响应时间(分钟)</div>
        </div>

        <!-- 待处理消息 -->
        <div class="border border-red-200 rounded-lg from-red-50 to-red-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-red-600 font-bold">{{ statistics.byStatus['待发送'] || 0 }}</div>
          <div class="mt-1 text-sm text-red-500">待发送消息</div>
        </div>
      </div>

      <!-- 详细统计 -->
      <div class="grid grid-cols-1 mt-6 gap-6 md:grid-cols-3">
        <!-- 消息类型分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:message-outline class="text-blue-500" />
            消息类型分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, type) in statistics.byType" :key="type" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: typeColors[type] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ type }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 消息状态分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:progress-check class="text-green-500" />
            消息状态分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, status) in statistics.byStatus" :key="status" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: statusColors[status] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ status }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 紧急程度分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:alert-circle-outline class="text-orange-500" />
            紧急程度分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, urgency) in statistics.byUrgency" :key="urgency" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div
                  class="h-3 w-3 rounded-full"
                  :style="{ 
                  backgroundColor: urgency === '非常紧急' ? '#f5222d' : 
                                  urgency === '高级' ? '#fa8c16' : 
                                  urgency === '中级'
                            ? '#52c41a'
                            : urgency === '低级'
                              ? '#91d5ff'
                              : '#d9d9d9'
                  }"
                ></div>
                <span class="text-sm text-gray-600">{{ urgency }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </NCard>

    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:device:message:add"
        delete-auth="t:device:message:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      />
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="962"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
      <DeviceMessageOperateDrawer
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
    </NCard>
  </div>
</template>

<style scoped>
/* 确保工具提示的边框样式正确显示，彻底去除黑色边框 */
:deep(.n-tooltip__content) {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

:deep(.n-tooltip) {
  border: none !important;
  outline: none !important;
}

:deep(.n-tooltip .n-tooltip__content) {
  border: none !important;
  outline: none !important;
  background: transparent !important;
}

/* 美化的状态指示器动画效果 */
.status-indicator {
  @apply inline-block w-2 h-2 rounded-full;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 响应式设计：在小屏幕上调整提示框宽度 */
@media (max-width: 640px) {
  .max-w-80 {
    max-width: 16rem;
  }
}
</style>
