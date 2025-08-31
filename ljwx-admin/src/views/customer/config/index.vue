<script setup lang="tsx">
import { NButton, NPopconfirm, NUpload, NModal, NCard, NTag, NDescriptions, NDescriptionsItem, NAlert, type UploadFileInfo } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteCustomerConfig, fetchGetCustomerConfigList, fetchGetOrgUnitsTree } from '@/service/api';
import { request } from '@/service/request';
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
      render: row => (
        <div class="flex items-center justify-center gap-2">
          <span class={row.supportLicense ? 'text-green-600' : 'text-gray-400'}>
            {row.supportLicense ? '✓ 是' : '✗ 否'}
          </span>
        </div>
      )
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
      width: 280,
      minWidth: 280,
      render: row => (
        <div class="flex-center gap-4px flex-wrap">
          {hasAuth('t:customer:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:customer:config:license:status') && (
            <NButton type="info" quaternary size="small" onClick={() => viewLicense(row)}>
              许可证
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

// 许可证管理功能
const licenseModalVisible = ref(false);
const licenseData: Ref<any> = ref(null);
const licenseUploading = ref(false);

async function viewLicense(customer: Api.Customer.CustomerConfig) {
  try {
    const { error, data } = await request<any>({
      url: `/t_customer_config/license/status/${customer.id}`,
      method: 'GET'
    });
    
    if (!error && data) {
      licenseData.value = data;
      licenseModalVisible.value = true;
    } else {
      window.$message?.error('获取许可证信息失败');
    }
  } catch (err) {
    window.$message?.error('获取许可证信息异常');
  }
}

async function uploadLicense(options: { file: UploadFileInfo }) {
  licenseUploading.value = true;
  
  try {
    const formData = new FormData();
    formData.append('file', options.file.file as File);
    
    const { error, data } = await request<any>({
      url: '/api/license/upload',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    if (!error && data) {
      window.$message?.success('许可证上传成功');
      // 重新获取许可证信息
      if (licenseData.value?.customerId) {
        const customer = data.find((item: any) => item.id === licenseData.value.customerId);
        if (customer) {
          await viewLicense(customer);
        }
      }
    } else {
      window.$message?.error('许可证上传失败');
    }
  } catch (err) {
    window.$message?.error('许可证上传异常');
  } finally {
    licenseUploading.value = false;
  }
  
  return false; // 阻止默认上传行为
}
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
      <CustomerConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" :customer-id="customerId" @submitted="getDataByPage" />
    </NCard>
    
    <!-- 许可证管理模态框 -->
    <NModal
      v-model:show="licenseModalVisible"
      preset="card"
      title="许可证管理"
      class="w-800px max-w-90vw"
    >
      <div v-if="licenseData" class="space-y-4">
        <!-- 许可证状态概览 -->
        <NAlert
          :type="getLicenseAlertType(licenseData.status)"
          :title="`许可证状态: ${getLicenseStatusText(licenseData.status)}`"
          :show-icon="true"
        >
          <div class="mt-2">
            <p v-if="licenseData.message">{{ licenseData.message }}</p>
            <p v-if="licenseData.daysLeft !== undefined">
              <span v-if="licenseData.daysLeft >= 0">剩余天数: {{ licenseData.daysLeft }} 天</span>
              <span v-else class="text-red-500">已过期: {{ Math.abs(licenseData.daysLeft) }} 天</span>
            </p>
          </div>
        </NAlert>
        
        <!-- 客户许可证配置 -->
        <NCard title="客户许可证配置" size="small">
          <NDescriptions :column="2" size="small">
            <NDescriptionsItem label="客户ID">{{ licenseData.customerId }}</NDescriptionsItem>
            <NDescriptionsItem label="客户支持许可证">
              <NTag :type="licenseData.customerSupportLicense ? 'success' : 'default'">
                {{ licenseData.customerSupportLicense ? '是' : '否' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="系统许可证启用">
              <NTag :type="licenseData.systemLicenseEnabled ? 'success' : 'default'">
                {{ licenseData.systemLicenseEnabled ? '是' : '否' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="系统许可证有效">
              <NTag :type="licenseData.systemLicenseValid ? 'success' : 'error'">
                {{ licenseData.systemLicenseValid ? '有效' : '无效' }}
              </NTag>
            </NDescriptionsItem>
          </NDescriptions>
        </NCard>
        
        <!-- 许可证详细信息 -->
        <NCard v-if="licenseData.licenseInfo" title="许可证详细信息" size="small">
          <NDescriptions :column="2" size="small">
            <NDescriptionsItem label="许可证ID">{{ licenseData.licenseInfo.licenseId }}</NDescriptionsItem>
            <NDescriptionsItem label="客户名称">{{ licenseData.licenseInfo.customer }}</NDescriptionsItem>
            <NDescriptionsItem label="最大用户数">{{ licenseData.licenseInfo.maxUsers }}</NDescriptionsItem>
            <NDescriptionsItem label="最大设备数">{{ licenseData.licenseInfo.maxDevices }}</NDescriptionsItem>
            <NDescriptionsItem label="签发时间">{{ formatDateTime(licenseData.licenseInfo.issueDate) }}</NDescriptionsItem>
            <NDescriptionsItem label="到期时间">{{ formatDateTime(licenseData.licenseInfo.expirationDate) }}</NDescriptionsItem>
            <NDescriptionsItem label="授权功能" :span="2">
              <div class="flex gap-2 flex-wrap">
                <NTag v-for="feature in licenseData.licenseInfo.features" :key="feature" size="small">
                  {{ feature }}
                </NTag>
              </div>
            </NDescriptionsItem>
          </NDescriptions>
        </NCard>
        
        <!-- 许可证文件上传 -->
        <NCard title="上传新许可证" size="small">
          <div class="space-y-4">
            <NUpload
              :custom-request="uploadLicense"
              :show-file-list="true"
              accept=".lic"
              :max="1"
              :disabled="licenseUploading"
            >
              <NButton :loading="licenseUploading" type="primary" size="small">
                {{ licenseUploading ? '上传中...' : '选择许可证文件' }}
              </NButton>
            </NUpload>
            <div class="text-sm text-gray-500">
              <p>• 支持 .lic 格式的许可证文件</p>
              <p>• 上传新许可证后将自动重新验证</p>
              <p>• 建议在更新前备份当前配置</p>
            </div>
          </div>
        </NCard>
      </div>
    </NModal>
  </div>
</template>

<script lang="ts">
// 辅助函数
function getLicenseAlertType(status: string): 'success' | 'info' | 'warning' | 'error' {
  switch (status) {
    case 'VALID': return 'success';
    case 'WARNING': return 'warning';
    case 'EXPIRED': return 'error';
    case 'INVALID': return 'error';
    case 'DISABLED': return 'info';
    default: return 'error';
  }
}

function getLicenseStatusText(status: string): string {
  switch (status) {
    case 'VALID': return '有效';
    case 'WARNING': return '即将过期';
    case 'EXPIRED': return '已过期';
    case 'INVALID': return '无效';
    case 'DISABLED': return '未启用';
    case 'ERROR': return '错误';
    default: return '未知';
  }
}

function formatDateTime(dateTime: string | null): string {
  if (!dateTime) return '-';
  try {
    return new Date(dateTime).toLocaleString('zh-CN');
  } catch {
    return dateTime;
  }
}
</script>
