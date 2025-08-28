<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteCustomerConfig, fetchGetCustomerConfigList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import CustomerConfigSearch from './modules/customer-config-search.vue';
import CustomerConfigOperateDrawer from './modules/customer-config-operate-drawer.vue';

defineOptions({
  name: 'TCustomerConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.CustomerConfig | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetCustomerConfigList,
  apiParams: {
    page: 1,
    pageSize: 20,
    id: customerId
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'id',
      title: '租户ID',
      align: 'center',
      minWidth: 150
    },
    {
      key: 'customerName',
      title: '租户名称',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'description',
      title: '租户描述',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'uploadMethod',
      title: '上传方法',
      align: 'center',
      minWidth: 100,
      render: row => dictTag('upload_method', row.uploadMethod)
    },
    {
      key: 'licenseKey',
      title: '许可证',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'supportLicense',
      title: '支持许可证',
      align: 'center',
      minWidth: 100,
      render: row => (row.supportLicense ? '是' : '否')
    },
    {
      key: 'enableResume',
      title: '是否启用续传',
      align: 'center',
      minWidth: 100,
      render: row => (row.enableResume ? '是' : '否')
    },
    {
      key: 'uploadRetryCount',
      title: '上传重试次数',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'cacheMaxCount',
      title: '缓存最大数量',
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
          {hasAuth('t:customer:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:customer:config:delete') && (
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

function edit(item: Api.Customer.CustomerConfig) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteCustomerConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteCustomerConfig(transDeleteParams(checkedRowKeys.value));
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
    <CustomerConfigSearch v-model:model="searchParams" :org-units-name="orgUnitsName" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:customer:config:add"
        delete-auth="t:customer:config:delete"
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
      <CustomerConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
