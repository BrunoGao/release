<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteDeviceConfig, fetchGetDeviceConfigList } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import DeviceConfigSearch from './modules/device-config-search.vue';
import DeviceConfigOperateDrawer from './modules/device-config-operate-drawer.vue';

defineOptions({
  name: 'TDeviceConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.DeviceConfig | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetDeviceConfigList,
  apiParams: {
    page: 1,
    pageSize: 20,
    logo: null
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'httpurl',
      title: $t('page.health.device.config.httpurl'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'logo',
      title: $t('page.health.device.config.logo'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'uitype',
      title: $t('page.health.device.config.uitype'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'heartratemeasureperiod',
      title: $t('page.health.device.config.heartratemeasureperiod'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'stressmonitoringenabled',
      title: $t('page.health.device.config.stressmonitoringenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'stepsmonitoringenabled',
      title: $t('page.health.device.config.stepsmonitoringenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'distancemonitoringenabled',
      title: $t('page.health.device.config.distancemonitoringenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'caloriemonitoringenabled',
      title: $t('page.health.device.config.caloriemonitoringenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'sleepmonitoringenabled',
      title: $t('page.health.device.config.sleepmonitoringenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'soseventlistenerenabled',
      title: $t('page.health.device.config.soseventlistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'doubleclickeventlistenerenabled',
      title: $t('page.health.device.config.doubleclickeventlistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'temperatureabnormallistenerenabled',
      title: $t('page.health.device.config.temperatureabnormallistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'heartrateabnormallistenerenabled',
      title: $t('page.health.device.config.heartrateabnormallistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'stressabnormallistenerenabled',
      title: $t('page.health.device.config.stressabnormallistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'falleventlistenerenabled',
      title: $t('page.health.device.config.falleventlistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'spo2abnormallistenerenabled',
      title: $t('page.health.device.config.spo2abnormallistenerenabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'oneclickalarmlistenerenabled',
      title: $t('page.health.device.config.oneclickalarmlistenerenabled'),
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
          {hasAuth('t:device:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:device:config:delete') && (
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

function edit(item: Api.Health.DeviceConfig) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteDeviceConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteDeviceConfig(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <DeviceConfigSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:device:config:add"
        delete-auth="t:device:config:delete"
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
      <DeviceConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
