<script setup lang="tsx">
import { NButton, NTabs, NTabPane, NCard, NPopconfirm, NDataTable } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { convertToBeijingTime } from '@/utils/date';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { 
  fetchDeleteAlertConfigWechat, 
  fetchGetAlertConfigWechatList
} from '@/service/api/health/alert-config-wechat';
import AlertConfigWechatSearch from './modules/alertconfigwechat-search.vue';
import AlertConfigWechatOperateDrawer from './modules/alert-config-wechat-operate-drawer.vue';

defineOptions({
  name: 'AlertConfigPage'
});

// 当前激活的tab
const activeTab = ref('enterprise');

// 企业微信配置
const enterpriseOperateType = ref<NaiveUI.TableOperateType>('add');
const enterpriseEditingData: Ref<Api.Health.AlertConfigWechat | null> = ref(null);

// 微信公众号配置
const officialOperateType = ref<NaiveUI.TableOperateType>('add');
const officialEditingData: Ref<Api.Health.AlertConfigWechat | null> = ref(null);

const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 企业微信表格配置
const {
  columns: enterpriseColumns,
  columnChecks: enterpriseColumnChecks,
  data: enterpriseData,
  loading: enterpriseLoading,
  getData: getEnterpriseData,
  getDataByPage: getEnterpriseDataByPage,
  mobilePagination: enterpriseMobilePagination,
  searchParams: enterpriseSearchParams,
  resetSearchParams: resetEnterpriseSearchParams
} = useTable({
  apiFn: fetchGetAlertConfigWechatList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    type: 'enterprise',
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
      render: row => row.agentId || '-'
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
      width: 150,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 120,
      minWidth: 120,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:wechat:alarm:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => editEnterprise(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:wechat:alarm:config:delete') && (
            <NPopconfirm onPositiveClick={() => handleDeleteEnterprise(row.id)}>
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

// 微信公众号表格配置
const {
  columns: officialColumns,
  columnChecks: officialColumnChecks,
  data: officialData,
  loading: officialLoading,
  getData: getOfficialData,
  getDataByPage: getOfficialDataByPage,
  mobilePagination: officialMobilePagination,
  searchParams: officialSearchParams,
  resetSearchParams: resetOfficialSearchParams
} = useTable({
  apiFn: fetchGetAlertConfigWechatList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    type: 'official',
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
      key: 'appid',
      title: 'AppID',
      align: 'center',
      width: 150,
      render: row => row.appid || '-'
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
      width: 150,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 120,
      minWidth: 120,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:wechat:alarm:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => editOfficial(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:wechat:alarm:config:delete') && (
            <NPopconfirm onPositiveClick={() => handleDeleteOfficial(row.id)}>
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

const { 
  drawerVisible: enterpriseDrawerVisible, 
  openDrawer: openEnterpriseDrawer, 
  checkedRowKeys: enterpriseCheckedRowKeys, 
  onDeleted: onEnterpriseDeleted, 
  onBatchDeleted: onEnterpriseBatchDeleted 
} = useTableOperate(enterpriseData, getEnterpriseData);

const { 
  drawerVisible: officialDrawerVisible, 
  openDrawer: openOfficialDrawer, 
  checkedRowKeys: officialCheckedRowKeys, 
  onDeleted: onOfficialDeleted, 
  onBatchDeleted: onOfficialBatchDeleted 
} = useTableOperate(officialData, getOfficialData);

// 企业微信操作
function handleAddEnterprise() {
  enterpriseOperateType.value = 'add';
  openEnterpriseDrawer();
}

function editEnterprise(item: Api.Health.AlertConfigWechat) {
  enterpriseOperateType.value = 'edit';
  enterpriseEditingData.value = { ...item };
  openEnterpriseDrawer();
}

async function handleDeleteEnterprise(id: string) {
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams([id]));
  if (!error && result) {
    await onEnterpriseDeleted();
  }
}

async function handleEnterpriseBatchDelete() {
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams(enterpriseCheckedRowKeys.value));
  if (!error && result) {
    await onEnterpriseBatchDeleted();
  }
}

// 微信公众号操作
function handleAddOfficial() {
  officialOperateType.value = 'add';
  openOfficialDrawer();
}

function editOfficial(item: Api.Health.AlertConfigWechat) {
  officialOperateType.value = 'edit';
  officialEditingData.value = { ...item };
  openOfficialDrawer();
}

async function handleDeleteOfficial(id: string) {
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams([id]));
  if (!error && result) {
    await onOfficialDeleted();
  }
}

async function handleOfficialBatchDelete() {
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams(officialCheckedRowKeys.value));
  if (!error && result) {
    await onOfficialBatchDeleted();
  }
}

// Tab切换时重新加载数据
function handleTabChange(value: string) {
  activeTab.value = value;
  if (value === 'enterprise') {
    getEnterpriseData();
  } else if (value === 'official') {
    getOfficialData();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" class="card-wrapper">
      <NTabs v-model:value="activeTab" type="line" @update:value="handleTabChange">
        <!-- 企业微信配置 -->
        <NTabPane name="enterprise" tab="企业微信配置">
          <div class="flex-col-stretch gap-8px">
            <AlertConfigWechatSearch 
              v-model:model="enterpriseSearchParams" 
              type="enterprise"
              @reset="resetEnterpriseSearchParams" 
              @search="getEnterpriseDataByPage" 
            />
            <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
              <TableHeaderOperation
                v-model:columns="enterpriseColumnChecks"
                :checked-row-keys="enterpriseCheckedRowKeys"
                :loading="enterpriseLoading"
                add-auth="t:wechat:alarm:config:add"
                delete-auth="t:wechat:alarm:config:delete"
                @add="handleAddEnterprise"
                @delete="handleEnterpriseBatchDelete"
                @refresh="getEnterpriseData"
              />
              <NDataTable
                v-model:checked-row-keys="enterpriseCheckedRowKeys"
                remote
                striped
                size="small"
                class="sm:h-full"
                :data="enterpriseData"
                :scroll-x="962"
                :columns="enterpriseColumns"
                :flex-height="!appStore.isMobile"
                :loading="enterpriseLoading"
                :single-line="false"
                :row-key="row => row.id"
                :pagination="enterpriseMobilePagination"
              />
            </NCard>
          </div>
        </NTabPane>

        <!-- 微信公众号配置 -->
        <NTabPane name="official" tab="微信公众号配置">
          <div class="flex-col-stretch gap-8px">
            <AlertConfigWechatSearch 
              v-model:model="officialSearchParams" 
              type="official"
              @reset="resetOfficialSearchParams" 
              @search="getOfficialDataByPage" 
            />
            <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
              <TableHeaderOperation
                v-model:columns="officialColumnChecks"
                :checked-row-keys="officialCheckedRowKeys"
                :loading="officialLoading"
                add-auth="t:wechat:alarm:config:add"
                delete-auth="t:wechat:alarm:config:delete"
                @add="handleAddOfficial"
                @delete="handleOfficialBatchDelete"
                @refresh="getOfficialData"
              />
              <NDataTable
                v-model:checked-row-keys="officialCheckedRowKeys"
                remote
                striped
                size="small"
                class="sm:h-full"
                :data="officialData"
                :scroll-x="962"
                :columns="officialColumns"
                :flex-height="!appStore.isMobile"
                :loading="officialLoading"
                :single-line="false"
                :row-key="row => row.id"
                :pagination="officialMobilePagination"
              />
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </NCard>

    <!-- 弹窗 -->
    <AlertConfigWechatOperateDrawer
      v-model:visible="enterpriseDrawerVisible"
      :operate-type="enterpriseOperateType"
      :row-data="enterpriseEditingData"
      type="enterprise"
      @submitted="getEnterpriseDataByPage"
    />
    
    <AlertConfigWechatOperateDrawer
      v-model:visible="officialDrawerVisible"
      :operate-type="officialOperateType"
      :row-data="officialEditingData"
      type="official"
      @submitted="getOfficialDataByPage"
    />
  </div>
</template>

<style scoped>
.card-wrapper {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
</style>