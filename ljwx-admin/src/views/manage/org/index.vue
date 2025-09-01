<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, ref } from 'vue';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { fetchDeleteOrgUnits, fetchGetOrgUnitsPageList, fetchGetOrgUnitsPageListOptimized } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { transDeleteParams } from '@/utils/common';
import { useDict } from '@/hooks/business/dict';
import OrgUnitsOperateDrawer, { type OperateType } from './modules/org-units-operate-drawer.vue';
import OrgUnitsSearch from './modules/org-units-search.vue';

defineOptions({
  name: 'OrgUnitsPage'
});

const appStore = useAppStore();

const { hasAuth } = useAuth();

const authStore = useAuthStore();

const { dictTag } = useDict();

// 判断是否是超级管理员（admin用户，可以管理所有租户）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 判断是否是租户管理员（只能管理自己租户）
const isTenantAdmin = computed(() => {
  return authStore.userInfo?.roleIds?.includes('R_ADMIN') && !isAdmin.value;
});

const operateType = ref<OperateType>('add');

const editingData: Ref<Api.SystemManage.OrgUnits | null> = ref(null);

// 获取customerId
const customerId = computed(() => authStore.userInfo?.customerId || 0);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetOrgUnitsPageListOptimized,
  apiParams: {
    page: 1,
    pageSize: 20,
    name: null,
    status: null,
    customerId: customerId.value
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
      title: isAdmin.value ? $t('page.manage.orgUnits.name') : $t('page.manage.orgUnits.dept.name'),
      align: 'center',
      width: 150,
      minWidth: 150
    },
    {
      key: 'code',
      title: isAdmin.value ? $t('page.manage.orgUnits.code') : $t('page.manage.orgUnits.dept.code'),
      align: 'center',
      width: 100,
      minWidth: 100
    },
    {
      key: 'abbr',
      title: isAdmin.value ? $t('page.manage.orgUnits.abbr') : $t('page.manage.orgUnits.dept.abbr'),
      align: 'center',
      width: 100,
      minWidth: 100
    },
    {
      key: 'description',
      title: isAdmin.value ? $t('page.manage.orgUnits.description') : $t('page.manage.orgUnits.dept.description'),
      align: 'center',
      width: 120,
      minWidth: 120
    },
    {
      key: 'sort',
      title: $t('page.manage.orgUnits.sort'),
      align: 'center',
      width: 50,
      minWidth: 50
    },
    {
      key: 'status',
      title: isAdmin.value ? $t('page.manage.orgUnits.status') : $t('page.manage.orgUnits.dept.status'),
      align: 'center',
      width: 60,
      minWidth: 60,
      render: row => dictTag('status', row.status)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 40,
      minWidth: 240,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('sys:org:units:add') && (
            <NButton type="primary" quaternary size="small" onClick={() => handleAddChildOrgUnits(row)}>
              {$t('page.manage.orgUnits.addChildOrgUnits')}
            </NButton>
          )}
          {hasAuth('sys:org:units:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('sys:org:units:delete') && (
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

function edit(item: Api.SystemManage.OrgUnits) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

async function handleAddChildOrgUnits(item: Api.SystemManage.OrgUnits) {
  operateType.value = 'addChild';
  editingData.value = { ...item };
  openDrawer();
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="mb-2">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-16px font-bold">{{ isAdmin ? '租户与部门管理' : '部门管理' }}</span>
          <span class="text-12px text-gray-500">
            {{ isAdmin ? '超级管理员可以创建租户和管理所有部门' : '租户管理员只能管理本租户下的部门' }}
          </span>
        </div>
      </template>
    </NCard>
    <OrgUnitsSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        :add-auth="isAdmin ? 'sys:org:units:add' : false"
        delete-auth="sys:org:units:delete"
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
      <OrgUnitsOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
