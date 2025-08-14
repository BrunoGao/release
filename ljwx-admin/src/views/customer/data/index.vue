<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, shallowRef } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteHealthDataConfig, fetchGetHealthDataConfigList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import HealthDataConfigSearch from './modules/health-data-config-search.vue';
import HealthDataConfigOperateDrawer from './modules/health-data-config-operate-drawer.vue';

defineOptions({
  name: 'THealthDataConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.HealthDataConfig | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetHealthDataConfigList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId: customerId ?? 0
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },

    {
      key: 'dataType',
      title: $t('page.customer.healthDataConfig.dataType'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'frequencyInterval',
      title: `${$t('page.customer.healthDataConfig.frequencyInterval')}(秒)`,
      align: 'center',
      minWidth: 100
    },
    {
      key: 'isEnabled',
      title: $t('page.customer.healthDataConfig.enabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningHigh',
      title: $t('page.customer.healthDataConfig.warningHigh'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningLow',
      title: $t('page.customer.healthDataConfig.warningLow'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningCnt',
      title: $t('page.customer.healthDataConfig.warningCnt'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'weight',
      title: $t('page.customer.healthDataConfig.weight'),
      align: 'center',
      minWidth: 100
    },

    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:health:data:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:health:data:config:delete') && (
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

function handleAdd() {}

function edit(item: Api.Customer.HealthDataConfig) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteHealthDataConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteHealthDataConfig(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
const orgUnitsName = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error: err, data: treeData }) => {
    if (!err && treeData) {
      // 提取 parentId 为 0 的选项
      orgUnitsName.value = treeData
        .filter(item => item.parentId === 0)
        .map(item => ({
          label: item.name,
          value: item.id
        }));
    }
  });
}
handleInitOptions();
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <HealthDataConfigSearch v-model:model="searchParams" :org-units-name="orgUnitsName" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:health:data:config:add"
        delete-auth="t:health:data:config:delete"
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
      <HealthDataConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
