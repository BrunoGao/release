<script setup lang="tsx">
import { NButton, NPopconfirm, NTooltip } from 'naive-ui';
import { type Ref, h, onMounted, ref, shallowRef, watch } from 'vue';
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
      key: 'departmentName',
      title: $t('page.health.device.info.orgName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'userId',
      title: $t('page.health.data.info.username'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'message',
      title: $t('page.health.device.message.message'),
      align: 'center',
      width: 400
    },
    {
      key: 'messageType',
      title: $t('page.health.device.message.messageType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('message_type', row.messageType)
    },
    {
      key: 'messageStatus',
      title: $t('page.health.device.message.messageStatus'),
      align: 'center',
      minWidth: 100,
      render: row => {
        let status = row.messageStatus;
        status = `已响应 [${row.respondedDetail?.respondedCount || 0}/${row.respondedDetail?.totalUsersWithDevices || 0}]`;

        // 创建美化的悬浮提示内容
        const nonRespondedUsers = row.respondedDetail?.nonRespondedUsers || [];
        const hasUsers = nonRespondedUsers.length > 0;
        
        const tooltipContent = h('div', { 
          class: 'max-w-80 p-3 bg-white shadow-lg rounded-lg border border-gray-100' 
        }, [
          // 标题
          h('div', { 
            class: 'flex items-center gap-2 mb-3 pb-2 border-b border-gray-100' 
          }, [
            h('div', { 
              class: `w-2 h-2 rounded-full ${hasUsers ? 'bg-orange-400' : 'bg-green-400'}` 
            }),
            h('span', { 
              class: 'font-semibold text-gray-800 text-sm' 
            }, hasUsers ? '未响应用户列表' : '响应状态')
          ]),
          
          // 内容区域
          hasUsers ? 
            h('div', { class: 'space-y-2 max-h-60 overflow-y-auto' }, [
              ...nonRespondedUsers.map(user => 
                h('div', { 
                  class: 'flex items-center justify-between p-2 bg-orange-50 rounded-md border-l-3 border-orange-400' 
                }, [
                  h('div', { class: 'flex flex-col' }, [
                    h('span', { class: 'text-sm font-medium text-gray-800' }, user.userName),
                    h('span', { class: 'text-xs text-gray-500' }, user.departmentName)
                  ]),
                  h('div', { 
                    class: 'w-2 h-2 rounded-full bg-orange-400' 
                  })
                ])
              ),
              // 如果用户太多，显示查看更多提示
              nonRespondedUsers.length > 5 && h('div', { 
                class: 'text-xs text-gray-400 text-center pt-2 border-t border-gray-100' 
              }, '向上滚动查看更多用户')
            ])
            :
            h('div', { 
              class: 'flex items-center gap-2 p-2 bg-green-50 rounded-md border-l-3 border-green-400' 
            }, [
              h('svg', { 
                class: 'w-4 h-4 text-green-500',
                fill: 'currentColor',
                viewBox: '0 0 20 20'
              }, [
                h('path', { 
                  'fill-rule': 'evenodd',
                  d: 'M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z',
                  'clip-rule': 'evenodd'
                })
              ]),
              h('span', { class: 'text-sm text-green-700' }, '所有用户均已响应')
            ])
        ]);

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
            trigger: () => h('span', { 
              class: 'cursor-pointer text-blue-600 hover:text-blue-800 transition-colors duration-200 underline decoration-dotted'
            }, status),
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
  0%, 100% {
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
