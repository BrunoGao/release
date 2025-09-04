<script setup lang="tsx">
import { computed } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import { $t } from '@/locales';
import { fetchDeletePosition, fetchGetPositionPageList } from '@/service/api';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { transDeleteParams } from '@/utils/common';
import { useDict } from '@/hooks/business/dict';
import PositionSearch from './modules/position-search.vue';
import PositionOperateDrawer from './modules/position-operate-drawer.vue';

defineOptions({
  name: 'PositionPage'
});

const appStore = useAppStore();

const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
console.log('customerId', customerId);
const { dictTag } = useDict();

// 判断是否是超级管理员（admin用户，可以管理所有租户的岗位）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetPositionPageList,
  apiParams: {
    page: 1,
    pageSize: 20,
    name: null,
    status: null,
    orgId: customerId,
    customerId: customerId
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'name',
      title: $t('page.manage.position.name'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'code',
      title: $t('page.manage.position.code'),
      align: 'center',
      minWidth: 200,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'abbr',
      title: $t('page.manage.position.abbr'),
      align: 'center',
      minWidth: 100
    },
    // 只有admin用户才显示租户列
    ...(isAdmin.value ? [{
      key: 'customerId',
      title: '租户ID',
      align: 'center',
      width: 100,
      render: row => row.customerId || '全局'
    }] : []),
    {
      key: 'weight',
      title: $t('page.manage.position.weight'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'description',
      title: $t('page.manage.position.description'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'sort',
      title: $t('page.manage.position.sort'),
      align: 'center',
      width: 80,
      minWidth: 80
    },
    {
      key: 'status',
      title: $t('page.manage.position.status'),
      align: 'center',
      width: 80,
      render: row => dictTag('status', row.status)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('sys:position:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('sys:position:delete') && (
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

const { drawerVisible, operateType, handleAdd, handleEdit, editingData, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function edit(id: string) {
  handleEdit(id);
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeletePosition(transDeleteParams([id]));
  if (!error && result) {
    onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeletePosition(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    onBatchDeleted();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <PositionSearch v-model:model="searchParams" :customer-id="customerId" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        :customer-id="customerId"
        add-auth="sys:position:add"
        delete-auth="sys:position:delete"
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
      <PositionOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :customer-id="customerId"
        :is-admin="isAdmin"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
