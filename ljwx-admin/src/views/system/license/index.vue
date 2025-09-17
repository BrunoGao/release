<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  NBadge,
  NButton,
  NCard,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NIcon,
  NInput,
  NModal,
  NP,
  NText,
  NUpload,
  NUploadDragger,
  useDialog,
  useMessage
} from 'naive-ui';
import { CheckmarkCircleOutline, CloseCircleOutline, CloudUploadOutline, RefreshOutline, SearchOutline } from '@vicons/ionicons5';
import type { DataTableColumns } from 'naive-ui';
import { formatDate } from '@/utils/date';
import { hasPermission } from '@/utils/auth';

// 响应式数据
const loading = ref(false);
const tableLoading = ref(false);
const revalidating = ref(false);
const toggling = ref(false);
const showImportModal = ref(false);
const showTenantStatusModal = ref(false);
const uploadRef = ref();
const selectedFile = ref<File | null>(null);
const selectedTenant = ref<any>(null);
const searchQuery = ref('');

// 系统状态
const systemStatus = ref({
  licenseEnabled: false,
  licenseValid: false,
  globalEnabled: true,
  licenseInfo: null as any,
  remainingDays: 0,
  totalTenants: 0,
  enabledTenants: 0
});

// 使用统计
const statistics = ref({
  totalTenants: 0,
  enabledTenants: 0,
  currentDevices: 0,
  deviceUsageRate: 0,
  maxDevices: 0
});

// 租户列表
const tenantList = ref([]);
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
});

// 消息提示
const message = useMessage();
const dialog = useDialog();

// 租户表格列定义
const tenantColumns: DataTableColumns = [
  {
    title: '租户名称',
    key: 'customerName',
    width: 200
  },
  {
    title: 'License支持',
    key: 'supportLicense',
    width: 120,
    render: (row: any) => {
      const type = row.supportLicense ? 'success' : 'error';
      const text = row.supportLicense ? '已启用' : '未启用';
      return h(NBadge, { type, text });
    }
  },
  {
    title: '当前设备数',
    key: 'currentDevices',
    width: 120,
    render: (row: any) => row.currentDevices || 0
  },
  {
    title: 'License状态',
    key: 'licenseStatus',
    width: 120,
    render: (row: any) => {
      const effective = row.licenseStatus?.effectiveLicenseEnabled;
      const type = effective ? 'success' : 'error';
      const text = effective ? '有效' : '无效';
      return h(NBadge, { type, text });
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row: any) => {
      return h('div', { class: 'action-buttons' }, [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => viewTenantStatus(row)
          },
          '查看状态'
        ),
        h(
          NButton,
          {
            size: 'small',
            type: row.supportLicense ? 'error' : 'success',
            style: { marginLeft: '8px' },
            onClick: () => toggleTenantLicense(row),
            disabled: !hasPermission('license:tenant:toggle')
          },
          row.supportLicense ? '禁用' : '启用'
        )
      ]);
    }
  }
];

// 计算属性
const getRemainingDaysType = (days: number) => {
  if (days > 30) return 'success';
  if (days > 7) return 'warning';
  return 'error';
};

// 生命周期
onMounted(() => {
  loadData();
});

// 方法
const refreshData = () => {
  loadData();
};

const loadData = async () => {
  loading.value = true;
  try {
    await Promise.all([loadSystemStatus(), loadStatistics(), loadTenantList()]);
  } catch (error) {
    console.error('加载数据失败:', error);
    message.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

const loadSystemStatus = async () => {
  try {
    const response = await fetch('/api/license/management/status');
    const data = await response.json();
    if (data.success) {
      systemStatus.value = data.data;
    }
  } catch (error) {
    console.error('加载系统状态失败:', error);
  }
};

const loadStatistics = async () => {
  try {
    const response = await fetch('/api/license/management/statistics');
    const data = await response.json();
    if (data.success) {
      statistics.value = data.data;
    }
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
};

const loadTenantList = async () => {
  tableLoading.value = true;
  try {
    const params = new URLSearchParams({
      pageNum: pagination.value.page.toString(),
      pageSize: pagination.value.pageSize.toString()
    });

    if (searchQuery.value) {
      params.append('customerName', searchQuery.value);
    }

    const response = await fetch(`/api/license/management/tenant/list?${params}`);
    const data = await response.json();

    if (data.success) {
      tenantList.value = data.rows || [];
      pagination.value.itemCount = data.total || 0;
    }
  } catch (error) {
    console.error('加载租户列表失败:', error);
  } finally {
    tableLoading.value = false;
  }
};

const revalidateLicense = async () => {
  revalidating.value = true;
  try {
    const response = await fetch('/api/license/management/revalidate', {
      method: 'POST'
    });
    const data = await response.json();

    if (data.success) {
      message.success('License重新验证成功');
      await loadSystemStatus();
    } else {
      message.error(data.message || 'License重新验证失败');
    }
  } catch (error) {
    message.error('License重新验证失败');
  } finally {
    revalidating.value = false;
  }
};

const toggleGlobalLicense = async () => {
  const action = systemStatus.value.globalEnabled ? '禁用' : '启用';

  dialog.warning({
    title: `确认${action}License功能`,
    content: `确定要全局${action}License功能吗？这将影响所有租户的License验证。`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      toggling.value = true;
      try {
        const enabled = !systemStatus.value.globalEnabled;
        const response = await fetch(`/api/license/management/toggle/${enabled}`, {
          method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
          message.success(`License功能已全局${action}`);
          await loadSystemStatus();
        } else {
          message.error(data.message || `${action}失败`);
        }
      } catch (error) {
        message.error(`${action}失败`);
      } finally {
        toggling.value = false;
      }
    }
  });
};

const handleFileChange = ({ file }: any) => {
  selectedFile.value = file.file;
};

const handleImportLicense = async () => {
  if (!selectedFile.value) {
    message.error('请选择License文件');
    return false;
  }

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);

    const response = await fetch('/api/license/management/import', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();

    if (data.success) {
      message.success('License导入成功');
      showImportModal.value = false;
      selectedFile.value = null;
      uploadRef.value?.clear();
      await loadData();
    } else {
      message.error(data.message || 'License导入失败');
      return false;
    }
  } catch (error) {
    message.error('License导入失败');
    return false;
  }
};

const viewTenantStatus = (tenant: any) => {
  selectedTenant.value = tenant;
  showTenantStatusModal.value = true;
};

const toggleTenantLicense = async (tenant: any) => {
  const action = tenant.supportLicense ? '禁用' : '启用';

  dialog.warning({
    title: `确认${action}租户License`,
    content: `确定要为租户"${tenant.customerName}"${action}License功能吗？`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const enabled = !tenant.supportLicense;
        const response = await fetch(`/api/license/management/tenant/${tenant.customerId}/toggle/${enabled}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
          message.success(`租户License已${action}`);
          await loadTenantList();
        } else {
          message.error(data.message || `${action}失败`);
        }
      } catch (error) {
        message.error(`${action}失败`);
      }
    }
  });
};

const handleSearch = () => {
  pagination.value.page = 1;
  loadTenantList();
};

const handlePageChange = (page: number) => {
  pagination.value.page = page;
  loadTenantList();
};

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize;
  pagination.value.page = 1;
  loadTenantList();
};
</script>

<template>
  <div class="license-management">
    <!-- 页面头部 -->
    <div class="header-section">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">🔐 License 管理</h1>
          <p class="page-subtitle">管理系统License配置、租户权限和使用监控</p>
        </div>
        <div class="action-buttons">
          <NButton type="primary" :loading="loading" @click="refreshData">
            <template #icon>
              <NIcon><RefreshOutline /></NIcon>
            </template>
            刷新
          </NButton>
          <NButton v-if="hasPermission('license:management:import')" type="success" @click="showImportModal = true">
            <template #icon>
              <NIcon><CloudUploadOutline /></NIcon>
            </template>
            导入License
          </NButton>
        </div>
      </div>
    </div>

    <!-- 系统License状态卡片 -->
    <div class="status-cards">
      <NCard title="📋 License 状态" class="status-card">
        <div class="license-status">
          <div class="status-indicator">
            <NBadge :type="systemStatus.licenseValid ? 'success' : 'error'" :text="systemStatus.licenseValid ? '有效' : '无效'" />
            <span class="status-text">
              {{ systemStatus.licenseValid ? 'License 正常运行' : 'License 异常或过期' }}
            </span>
          </div>

          <div v-if="systemStatus.licenseInfo" class="license-info">
            <NDescriptions :column="2" bordered>
              <NDescriptionsItem label="客户名称">
                {{ systemStatus.licenseInfo.customerName || '--' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="许可证类型">
                {{ systemStatus.licenseInfo.licenseType || '--' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="最大设备数">
                {{ systemStatus.licenseInfo.maxDevices || '--' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="最大用户数">
                {{ systemStatus.licenseInfo.maxUsers || '--' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="到期日期">
                {{ formatDate(systemStatus.licenseInfo.endDate) }}
              </NDescriptionsItem>
              <NDescriptionsItem label="剩余天数">
                <NBadge :type="getRemainingDaysType(systemStatus.remainingDays)" :text="systemStatus.remainingDays + ' 天'" />
              </NDescriptionsItem>
            </NDescriptions>
          </div>

          <div class="license-actions">
            <NButton v-if="hasPermission('license:management:revalidate')" type="warning" :loading="revalidating" @click="revalidateLicense">
              重新验证
            </NButton>
            <NButton
              v-if="hasPermission('license:management:toggle')"
              :type="systemStatus.globalEnabled ? 'error' : 'success'"
              :loading="toggling"
              @click="toggleGlobalLicense"
            >
              {{ systemStatus.globalEnabled ? '全局禁用' : '全局启用' }}
            </NButton>
          </div>
        </div>
      </NCard>

      <NCard title="📊 使用统计" class="status-card">
        <div class="usage-stats">
          <div class="stat-item">
            <div class="stat-value">{{ statistics.totalTenants || 0 }}</div>
            <div class="stat-label">总租户数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.enabledTenants || 0 }}</div>
            <div class="stat-label">已启用租户</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.currentDevices || 0 }}</div>
            <div class="stat-label">当前设备数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.deviceUsageRate || 0 }}%</div>
            <div class="stat-label">设备使用率</div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 租户License管理 -->
    <NCard title="👥 租户License管理" class="tenant-management">
      <template #header-extra>
        <NInput v-model:value="searchQuery" placeholder="搜索租户名称" clearable style="width: 250px" @input="handleSearch">
          <template #prefix>
            <NIcon><SearchOutline /></NIcon>
          </template>
        </NInput>
      </template>

      <NDataTable
        :columns="tenantColumns"
        :data="tenantList"
        :loading="tableLoading"
        :pagination="pagination"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </NCard>

    <!-- License导入弹窗 -->
    <NModal
      v-model:show="showImportModal"
      preset="dialog"
      title="导入License文件"
      positive-text="导入"
      negative-text="取消"
      @positive-click="handleImportLicense"
      @negative-click="showImportModal = false"
    >
      <div class="import-content">
        <NUpload ref="uploadRef" :max="1" accept=".lic" :show-file-list="true" :default-upload="false" @change="handleFileChange">
          <NUploadDragger>
            <div style="margin-bottom: 12px">
              <NIcon size="48" :depth="3">
                <CloudUploadOutline />
              </NIcon>
            </div>
            <NText style="font-size: 16px">点击或者拖动License文件到该区域来上传</NText>
            <NP depth="3" style="margin: 8px 0 0 0">支持.lic格式的License文件，文件大小不超过10MB</NP>
          </NUploadDragger>
        </NUpload>
      </div>
    </NModal>

    <!-- 租户License状态弹窗 -->
    <NModal v-model:show="showTenantStatusModal" preset="card" title="租户License状态" style="width: 600px" @after-leave="selectedTenant = null">
      <div v-if="selectedTenant">
        <NDescriptions :column="1" bordered>
          <NDescriptionsItem label="租户名称">
            {{ selectedTenant.customerName }}
          </NDescriptionsItem>
          <NDescriptionsItem label="License支持">
            <NBadge :type="selectedTenant.supportLicense ? 'success' : 'error'" :text="selectedTenant.supportLicense ? '已启用' : '未启用'" />
          </NDescriptionsItem>
          <NDescriptionsItem label="系统License状态">
            <NBadge
              :type="selectedTenant.licenseStatus?.systemLicenseValid ? 'success' : 'error'"
              :text="selectedTenant.licenseStatus?.systemLicenseValid ? '有效' : '无效'"
            />
          </NDescriptionsItem>
          <NDescriptionsItem label="有效License状态">
            <NBadge
              :type="selectedTenant.licenseStatus?.effectiveLicenseEnabled ? 'success' : 'error'"
              :text="selectedTenant.licenseStatus?.effectiveLicenseEnabled ? '启用' : '禁用'"
            />
          </NDescriptionsItem>
          <NDescriptionsItem label="当前设备数">
            {{ selectedTenant.currentDevices || 0 }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="selectedTenant.licenseStatus?.error" label="错误信息">
            <NText type="error">{{ selectedTenant.licenseStatus.error }}</NText>
          </NDescriptionsItem>
        </NDescriptions>
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.license-management {
  padding: 20px;
}

.header-section {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1a1a1a;
}

.page-subtitle {
  color: #666;
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.status-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.status-card {
  min-height: 200px;
}

.license-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-text {
  font-size: 16px;
  font-weight: 500;
}

.license-actions {
  display: flex;
  gap: 12px;
}

.usage-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.tenant-management {
  margin-bottom: 24px;
}

.import-content {
  padding: 20px 0;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .usage-stats {
    grid-template-columns: 1fr;
  }
}
</style>
