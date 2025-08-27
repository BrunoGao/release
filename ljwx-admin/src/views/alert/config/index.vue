<script setup lang="tsx">
import { NButton, NTabs, NTabPane, NCard, NPopconfirm, NDataTable } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, computed, watch, onMounted, h } from 'vue';
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
import TableHeaderOperation from '@/components/advanced/table-header-operation.vue';

defineOptions({
  name: 'AlertConfigPage'
});

// 当前激活的tab
const activeTab = ref('enterprise');

const operateType = ref<NaiveUI.TableOperateType>('add');
const editingData: Ref<Api.Health.AlertConfigWechat | null> = ref(null);

const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 企业微信列定义
const enterpriseColumns = computed(() => [
  { key: 'index', title: '序号', width: 64, align: 'center' },
  { key: 'corpId', title: '企业ID', align: 'center', width: 150, render: (row: any) => row.corpId || '-' },
  { key: 'agentId', title: '应用ID', align: 'center', width: 100, render: (row: any) => row.agentId || '-' },
  { key: 'secret', title: '应用Secret', align: 'center', width: 120, render: (row: any) => row.secret ? '***' + row.secret.slice(-4) : '-' },
  { key: 'templateId', title: '模板ID', align: 'center', width: 200, render: (row: any) => row.templateId || '-' },
  { key: 'enabled', title: '启用状态', align: 'center', width: 100, render: (row: any) => row.enabled ? '启用' : '禁用' },
  { key: 'createTime', title: '创建时间', align: 'center', width: 150, render: (row: any) => convertToBeijingTime(row.createTime) },
  { 
    key: 'operate', 
    title: '操作', 
    align: 'center', 
    width: 120, 
    render: (row: any) => {
      return h('div', { class: 'flex-center gap-8px' }, [
        hasAuth('t:wechat:alarm:config:update') && h(NButton, {
          type: 'primary',
          quaternary: true,
          size: 'small',
          onClick: () => edit(row)
        }, () => '编辑'),
        hasAuth('t:wechat:alarm:config:delete') && h(NPopconfirm, {
          onPositiveClick: () => handleDelete(row.id)
        }, {
          default: () => '确认删除？',
          trigger: () => h(NButton, {
            type: 'error',
            quaternary: true,
            size: 'small'
          }, () => '删除')
        })
      ].filter(Boolean));
    }
  }
]);

// 微信公众号列定义
const officialColumns = computed(() => [
  { key: 'index', title: '序号', width: 64, align: 'center' },
  { key: 'appid', title: 'AppID', align: 'center', width: 150, render: (row: any) => row.appid || '-' },
  { key: 'appsecret', title: 'AppSecret', align: 'center', width: 120, render: (row: any) => row.appsecret ? '***' + row.appsecret.slice(-4) : '-' },
  { key: 'wechatId', title: '微信ID', align: 'center', width: 120, render: (row: any) => row.appid || '-' },
  { key: 'templateId', title: '模板ID', align: 'center', width: 200, render: (row: any) => row.templateId || '-' },
  { key: 'enabled', title: '启用状态', align: 'center', width: 100, render: (row: any) => row.enabled ? '启用' : '禁用' },
  { key: 'createTime', title: '创建时间', align: 'center', width: 150, render: (row: any) => convertToBeijingTime(row.createTime) },
  { 
    key: 'operate', 
    title: '操作', 
    align: 'center', 
    width: 120, 
    render: (row: any) => {
      return h('div', { class: 'flex-center gap-8px' }, [
        hasAuth('t:wechat:alarm:config:update') && h(NButton, {
          type: 'primary',
          quaternary: true,
          size: 'small',
          onClick: () => edit(row)
        }, () => '编辑'),
        hasAuth('t:wechat:alarm:config:delete') && h(NPopconfirm, {
          onPositiveClick: () => handleDelete(row.id)
        }, {
          default: () => '确认删除？',
          trigger: () => h(NButton, {
            type: 'error',
            quaternary: true,
            size: 'small'
          }, () => '删除')
        })
      ].filter(Boolean));
    }
  }
]);

// 使用单个useTable
const { 
  columns, 
  columnChecks, 
  data, 
  loading, 
  getData, 
  getDataByPage, 
  mobilePagination, 
  searchParams, 
  updateSearchParams,
  resetSearchParams,
  reloadColumns
} = useTable({
  apiFn: fetchGetAlertConfigWechatList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    type: 'enterprise', // 明确设置初始type
    enabled: null
  },
  columns: () => {
    // 基础列
    const baseColumns = [
      {
        key: 'index',
        title: $t('common.index'),
        width: 64,
        align: 'center'
      }
    ];

    // 根据当前选中的类型显示不同的列
    const typeSpecificColumns = activeTab.value === 'enterprise' 
      ? [
          // 企业微信专属字段
          {
            key: 'corpId',
            title: '企业ID',
            align: 'center',
            width: 150,
            render: (row: any) => row.corpId || '-'
          },
          {
            key: 'agentId',
            title: '应用ID',
            align: 'center',
            width: 100,
            render: (row: any) => row.agentId || '-'
          },
          {
            key: 'secret',
            title: '应用Secret',
            align: 'center',
            width: 120,
            render: (row: any) => row.secret ? '***' + row.secret.slice(-4) : '-'
          }
        ]
      : [
          // 微信公众号专属字段
          {
            key: 'appid',
            title: 'AppID',
            align: 'center',
            width: 150,
            render: (row: any) => row.appid || '-'
          },
          {
            key: 'appsecret',
            title: 'AppSecret',
            align: 'center',
            width: 120,
            render: (row: any) => row.appsecret ? '***' + row.appsecret.slice(-4) : '-'
          },
          {
            key: 'wechatId',
            title: '微信ID',
            align: 'center',
            width: 120,
            render: (row: any) => row.appid || '-'  // 临时使用appid作为微信ID
          }
        ];

    // 通用列
    const commonColumns = [
      {
        key: 'templateId',
        title: '模板ID',
        align: 'center',
        width: 200,
        render: (row: any) => row.templateId || '-'
      },
      {
        key: 'enabled',
        title: '启用状态',
        align: 'center',
        width: 100,
        render: (row: any) => row.enabled ? '启用' : '禁用'
      },
      {
        key: 'createTime',
        title: $t('page.health.alert.config.wechat.createTime'),
        align: 'center',
        width: 150,
        render: (row: any) => convertToBeijingTime(row.createTime)
      },
      {
        key: 'operate',
        title: $t('common.operate'),
        align: 'center',
        width: 120,
        minWidth: 120,
        render: (row: any) => (
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
    ];

    return [...baseColumns, ...typeSpecificColumns, ...commonColumns];
  }
});

const { 
  drawerVisible, 
  openDrawer, 
  checkedRowKeys, 
  onDeleted, 
  onBatchDeleted 
} = useTableOperate(data, getData);

// 操作函数
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
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  const { error, data: result } = await fetchDeleteAlertConfigWechat(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}



// Tab切换时重新加载数据
function handleTabChange(value: string) {
  activeTab.value = value;
  
  // 使用updateSearchParams方法来确保参数正确更新
  updateSearchParams({
    type: value,
    page: 1,
    pageSize: searchParams.pageSize || 20,
    customerId
  });
  
  // 强制重新计算列定义
  reloadColumns();
  
  // 重新加载数据
  getData();
}

// 确保初始数据加载时使用正确的type
onMounted(() => {
  // 强制设置searchParams的type字段
  updateSearchParams({
    ...searchParams,
    type: activeTab.value,
    customerId
  });
  
  // 加载初始数据
  getData();
});

</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" class="card-wrapper">
      <NTabs v-model:value="activeTab" type="line" @update:value="handleTabChange">
        <!-- 企业微信配置 -->
        <NTabPane name="enterprise" tab="企业微信配置">
          <div class="flex-col-stretch gap-8px">
            <AlertConfigWechatSearch 
              v-model:model="searchParams" 
              type="enterprise"
              @reset="resetSearchParams" 
              @search="getDataByPage" 
            />
            <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div>
                  <NButton type="primary" @click="handleAdd" v-if="hasAuth('t:wechat:alarm:config:add')">
                    新增
                  </NButton>
                  <NButton type="error" @click="handleBatchDelete" :disabled="checkedRowKeys.length === 0" v-if="hasAuth('t:wechat:alarm:config:delete')" style="margin-left: 8px;">
                    批量删除
                  </NButton>
                </div>
                <NButton @click="getData" :loading="loading">
                  刷新
                </NButton>
              </div>
              
              
              <NDataTable
                v-model:checked-row-keys="checkedRowKeys"
                :data="data"
                :columns="enterpriseColumns"
                :row-key="(row: any) => row.id"
                size="small"
                striped
                :loading="loading"
              />
            </NCard>
          </div>
        </NTabPane>

        <!-- 微信公众号配置 -->
        <NTabPane name="official" tab="微信公众号配置">
          <div class="flex-col-stretch gap-8px">
            <AlertConfigWechatSearch 
              v-model:model="searchParams" 
              type="official"
              @reset="resetSearchParams" 
              @search="getDataByPage" 
            />
            <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div>
                  <NButton type="primary" @click="handleAdd" v-if="hasAuth('t:wechat:alarm:config:add')">
                    新增
                  </NButton>
                  <NButton type="error" @click="handleBatchDelete" :disabled="checkedRowKeys.length === 0" v-if="hasAuth('t:wechat:alarm:config:delete')" style="margin-left: 8px;">
                    批量删除
                  </NButton>
                </div>
                <NButton @click="getData" :loading="loading">
                  刷新
                </NButton>
              </div>
              
              
              <NDataTable
                v-model:checked-row-keys="checkedRowKeys"
                :data="data"
                :columns="officialColumns"
                :row-key="(row: any) => row.id"
                size="small"
                striped
                :loading="loading"
              />
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </NCard>


    <!-- 弹窗 -->
    <AlertConfigWechatOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      :type="activeTab"
      @submitted="getDataByPage"
    />
  </div>
</template>

<style scoped>
.card-wrapper {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
</style>