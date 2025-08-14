<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAlertRules, fetchGetAlertRulesList } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import AlerrulesSearch from './modules/alerrules-search.vue';
import AlerrulesOperateDrawer from './modules/alerrules-operate-drawer.vue';
defineOptions({
  name: 'TAlertRulesPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.AlertRules | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertRulesList,
  apiParams: {
    page: 1,
    pageSize: 20,
    ruleType: null,
    physicalSign: null
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
      key: 'ruleType',
      title: $t('page.health.alert.rules.ruleType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_type', row.ruleType)
    },
    {
      key: 'physicalSign',
      title: $t('page.health.alert.rules.physicalSign'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('health_data_type', row.physicalSign)
    },
    {
      key: 'thresholdMin',
      title: $t('page.health.alert.rules.thresholdMin'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'thresholdMax',
      title: $t('page.health.alert.rules.thresholdMax'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'trendDuration',
      title: $t('page.health.alert.rules.trendDuration'),
      align: 'center',
      minWidth: 100
    },

    {
      key: 'alertMessage',
      title: $t('page.health.alert.rules.alertMessage'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'notificationType',
      title: $t('page.health.alert.rules.notificationType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('notification_type', row.notificationType)
    },
    {
      key: 'severityLevel',
      title: $t('page.health.alert.rules.severityLevel'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_severityLevel', row.severityLevel)
    },
    {
      key: 'createUser',
      title: $t('page.health.alert.rules.createUser'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'createTime',
      title: $t('page.health.alert.rules.createTime'),
      align: 'center',
      minWidth: 100,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:alert:rules:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:alert:rules:delete') && (
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

function edit(item: Api.Health.AlertRules) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <AlerrulesSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:alert:rules:add"
        delete-auth="t:alert:rules:delete"
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
      <AlerrulesOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
