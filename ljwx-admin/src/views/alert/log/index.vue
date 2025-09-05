<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import { type Ref, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { formatDate } from '@/utils/date';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAleractionLog, fetchGetAleractionLogList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import AleractionLogSearch from './modules/aleraction-log-search.vue';
import AleractionLogOperateDrawer from './modules/aleraction-log-operate-drawer.vue';
defineOptions({
  name: 'TAlertActionLogPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.AleractionLog | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAleractionLogList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null
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
      key: 'logId',
      title: $t('page.health.alert.log.logId'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'alertId',
      title: $t('page.health.alert.log.alertId'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'action',
      title: $t('page.health.alert.log.action'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'details',
      title: $t('page.health.alert.log.details'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'result',
      title: $t('page.health.alert.log.result'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_result', row.result)
    },
    {
      key: 'actionUser',
      title: $t('page.health.alert.log.actionUser'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'actionTimestamp',
      title: $t('page.health.alert.log.actionTimestamp'),
      align: 'center',
      minWidth: 100,
      render: row => formatDate(row.actionTimestamp, 'YYYY-MM-DD HH:mm:ss')
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:alert:action:log:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:alert:action:log:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.logId)}>
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

function edit(item: Api.Health.AleractionLog) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: number) {
  // request
  const { error, data: result } = await fetchDeleteAleractionLog(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAleractionLog(transDeleteParams(checkedRowKeys.value));
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
      // 设置默认选中第一个部门
      if (treeData.length > 0) {
        searchParams.orgId = treeData[0].id;
        // 初始化时获取第一个部门的员工列表
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
    <AleractionLogSearch
      v-model:model="searchParams"
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
        add-auth="t:alert:action:log:add"
        delete-auth="t:alert:action:log:delete"
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
        :row-key="row => row.logId"
        :pagination="mobilePagination"
      />
      <AleractionLogOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
