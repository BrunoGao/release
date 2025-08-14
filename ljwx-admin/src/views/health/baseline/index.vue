<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import { type Ref, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteHealthBaseline, fetchGetHealthBaselineList, fetchGetOrgUnitsTree } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import HealthBaselineSearch from './modules/health-baseline-search.vue';
import HealthBaselineOperateDrawer from './modules/health-baseline-operate-drawer.vue';

defineOptions({
    name: 'THealthBaselinePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const { hasAuth } = useAuth();

const authStore = useAuthStore();

const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.HealthBaseline | null> = ref(null);

  const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();
const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
    apiFn: fetchGetHealthBaselineList,
    apiParams: {
        page: 1,
        pageSize: 20,
        customerId: customerId,
        orgId: null,
        userId: null,
        feature: null,
        startDate: startDate,
        endDate: endDate,
    },
    columns: () => [
        {
            key: 'index',
            title: $t('common.index'),
            width: 64,
            align: 'center'
        },
        {
            key: 'orgName',
            title: $t('page.health.data.baseline.orgName'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'userName',
            title: $t('page.health.data.baseline.userName'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'featureName',
            title: $t('page.health.data.baseline.featureName'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'baselineDate',
            title: $t('page.health.data.baseline.baselineDate'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'meanValue',
            title: $t('page.health.data.baseline.meanValue'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'stdValue',
            title: $t('page.health.data.baseline.stdValue'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'minValue',
            title: $t('page.health.data.baseline.minValue'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'maxValue',
            title: $t('page.health.data.baseline.maxValue'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'sampleCount',
            title: $t('page.health.data.baseline.sampleCount'),
            align: 'center',
            minWidth: 100
        },
        {
            key: 'baselineTime',
            title: $t('page.health.data.baseline.baselineTime'),
            align: 'center',
            minWidth: 100,
            render: row => convertToBeijingTime(row.baselineTime)
        },

        {
            key: 'operate',
            title: $t('common.operate'),
            align: 'center',
            width: 200,
            minWidth: 200,
            render: row => (
                <div class="flex-center gap-8px">
                    {hasAuth('t:health:baseline:update') && (
                        <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
                            {$t('common.edit')}
                        </NButton>
                    )}
                    {hasAuth('t:health:baseline:delete') && (
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

}

function edit(item: Api.Health.HealthBaseline) {
    operateType.value = 'edit';
    editingData.value = { ...item };
    openDrawer();
}

async function handleDelete(id: string) {
    // request
    const { error, data: result } = await fetchDeleteHealthBaseline(transDeleteParams([id]));
    if (!error && result) {
        await onDeleted();
    }
}

async function handleBatchDelete() {
    // request
    const { error, data: result } = await fetchDeleteHealthBaseline(transDeleteParams(checkedRowKeys.value));
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
    <HealthBaselineSearch v-model:model="searchParams" :org-units-tree="orgUnitsTree" :user-options="userOptions" :customer-id="customerId" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
        <TableHeaderOperation
            v-model:columns="columnChecks"
            :checked-row-keys="checkedRowKeys"
            :loading="loading"
            add-auth="t:health:baseline:add"
            delete-auth="t:health:baseline:delete"
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
        <HealthBaselineOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
</div>
</template>
