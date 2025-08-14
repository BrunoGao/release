<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, shallowRef } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteInterface, fetchGetInterfaceList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import InterfaceSearch from './modules/interface-search.vue';
import InterfaceOperateDrawer from './modules/interface-operate-drawer.vue';

defineOptions({
  name: 'TInterfacePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.Interface | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetInterfaceList,
  apiParams: {
    page: 1,
    pageSize: 20,
    name: null,
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
      key: 'name',
      title: $t('page.customer.interface.name'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'url',
      title: $t('page.customer.interface.url'),
      align: 'center',
      width: 500
    },
    {
      key: 'callInterval',
      title: `${$t('page.customer.interface.callInterval')}(秒)`,
      align: 'center',
      minWidth: 100
    },
    {
      key: 'method',
      title: $t('page.customer.interface.method'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'description',
      title: $t('page.customer.interface.description'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'apiId',
      title: $t('page.customer.interface.apiId'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'apiAuth',
      title: $t('page.customer.interface.apiAuth'),
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
          {hasAuth('t:interface:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:interface:delete') && (
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

function edit(item: Api.Customer.Interface) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  console.log(editingData.value);
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteInterface(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteInterface(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

/** org units tree data */
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
    <InterfaceSearch v-model:model="searchParams" :org-units-name="orgUnitsName" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:interface:add"
        delete-auth="t:interface:delete"
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
      <InterfaceOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
