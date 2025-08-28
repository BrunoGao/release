<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import { type Ref, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { fetchDeleteHealthScore, fetchGetHealthScoreList, fetchGetOrgUnitsTree } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';

import HealthScoreSearch from './modules/health-score-search.vue';
import HealthScoreOperateDrawer from './modules/health-score-operate-drawer.vue';

defineOptions({
  name: 'THealthScorePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const { hasAuth } = useAuth();
const authStore = useAuthStore();

const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.HealthScore | null> = ref(null);
const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetHealthScoreList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    feature: null,
    startDate,
    endDate
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
      title: $t('page.health.data.score.orgName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'userName',
      title: $t('page.health.data.score.userName'),
      align: 'center',
      minWidth: 100
    },

    {
      key: 'featureName',
      title: $t('page.health.data.score.featureName'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'avgValue',
      title: $t('page.health.data.score.avgValue'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'healthScore',
      title: $t('page.health.data.score.healthScore'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'weightedScore',
      title: $t('page.health.data.score.weightedScore'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'finalScore',
      title: $t('page.health.data.score.finalScore'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'featureWeight',
      title: $t('page.health.data.score.featureWeight'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'positionWeight',
      title: $t('page.health.data.score.positionWeight'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'baselineMean',
      title: $t('page.health.data.score.baselineMean'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'baselineStd',
      title: $t('page.health.data.score.baselineStd'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'currentValue',
      title: $t('page.health.data.score.currentValue'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'scoreValue',
      title: $t('page.health.data.score.scoreValue'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'penaltyValue',
      title: $t('page.health.data.score.penaltyValue'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'baselineTime',
      title: $t('page.health.data.score.baselineTime'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'scoreDate',
      title: $t('page.health.data.score.scoreDate'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'createTime',
      title: $t('page.health.data.score.createTime'),
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
          {hasAuth('t:health:score:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:health:score:delete') && (
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

function edit(item: Api.Health.HealthScore) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteHealthScore(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteHealthScore(transDeleteParams(checkedRowKeys.value));
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
    <HealthScoreSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      :customer-id="customerId"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:health:score:add"
        delete-auth="t:health:score:delete"
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
      <HealthScoreOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
