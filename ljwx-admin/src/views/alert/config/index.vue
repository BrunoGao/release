<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { convertToBeijingTime } from '@/utils/date';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAlertConfigWechat, fetchGetAlertConfigWechatList } from '@/service/api/health/alert-config-wechat';
import AlertConfigWechatSearch from './modules/alertconfigwechat-search.vue';
import AlertConfigWechatOperateDrawer from './modules/alert-config-wechat-operate-drawer.vue';

defineOptions({
  name: 'TWechatAlertConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const { hasAuth } = useAuth();

const authStore = useAuthStore();

const customerId = authStore.userInfo?.customerId;
const editingData: Ref<Api.Health.AlertConfigWechat | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertConfigWechatList,
  apiParams: {
    page: 1,
    pageSize: 20,
    tenantId: customerId,
    type: null,
    enabled: null
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'type',
      title: '微信类型',
      align: 'center',
      width: 120,
      render: row => row.type === 'enterprise' ? '企业微信' : '公众号'
    },
    {
      key: 'corpId',
      title: '企业ID',
      align: 'center',
      width: 150,
      render: row => row.corpId || '-'
    },
    {
      key: 'agentId',
      title: '应用ID',
      align: 'center',
      width: 100,
      render: row => row.agentId || row.appid || '-'
    },
    {
      key: 'templateId',
      title: '模板ID',
      align: 'center',
      width: 200,
      render: row => row.templateId || '-'
    },
    {
      key: 'enabled',
      title: '启用状态',
      align: 'center',
      width: 100,
      render: row => row.enabled ? '启用' : '禁用'
    },
    {
      key: 'createTime',
      title: $t('page.health.alert.config.wechat.createTime'),
      align: 'center',
      width: 100,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 100,
      minWidth: 100,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:wechat:alarm:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:wechat:alarm:config:delete') && (
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

function edit(item: Api.Health.AlertConfigWechat) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <AlertConfigWechatSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:wechat:alarm:config:add"
        delete-auth="t:wechat:alarm:config:delete"
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
      <AlertConfigWechatOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
