<script setup lang="ts">
import { NButton, NPopconfirm, NUpload, NModal, NCard, NTag, NDescriptions, NDescriptionsItem, NAlert, NCollapse, NCollapseItem, NList, NListItem, NIcon, NSpace, type UploadFileInfo } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, h, computed } from 'vue';
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

// 检查是否为管理员用户
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

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
      render: row => h('div', { class: 'flex items-center justify-center gap-2' }, [
        h('span', { 
          class: row.supportLicense ? 'text-green-600' : 'text-gray-400' 
        }, row.supportLicense ? '✓ 是' : '✗ 否')
      ])
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
      render: row => {
        const buttons = [];
        
        // 编辑按钮 - 只有admin可见
        if (hasAuth('t:customer:config:update') && isAdmin.value) {
          buttons.push(
            h(NButton, {
              type: 'primary',
              quaternary: true,
              size: 'small',
              onClick: () => edit(row)
            }, () => $t('common.edit'))
          );
        }
        
        // 许可证按钮 - 只有admin可见
        if (hasAuth('t:customer:config:license:status') && isAdmin.value) {
          buttons.push(
            h(NButton, {
              type: 'info',
              quaternary: true,
              size: 'small',
              onClick: () => viewLicense(row)
            }, () => '许可证')
          );
        }
        
        // 如果不是admin，显示提示信息
        if (!isAdmin.value && buttons.length === 0) {
          buttons.push(
            h('span', { 
              class: 'text-gray-400 text-xs px-2 py-1' 
            }, '仅管理员可操作')
          );
        }
        
        if (hasAuth('t:customer:config:delete') && isAdmin.value) {
          buttons.push(
            h(NPopconfirm, {
              onPositiveClick: () => handleDelete(row.id)
            }, {
              default: () => $t('common.confirmDelete'),
              trigger: () => h(NButton, {
                type: 'error',
                quaternary: true,
                size: 'small'
              }, () => $t('common.delete'))
            })
          );
        }
        
        return h('div', { class: 'flex-center gap-4px flex-wrap' }, buttons);
      }
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能添加租户配置');
    return;
  }
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Customer.CustomerConfig) {
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能编辑租户配置');
    return;
  }
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能删除租户配置');
    return;
  }
  // request
  const { error, data: result } = await fetchDeleteCustomerConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能批量删除租户配置');
    return;
  }
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

const manualExpanded = ref<string[]>([]);

async function viewLicense(customer: Api.Customer.CustomerConfig) {
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能查看许可证信息');
    return;
  }
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
  if (!isAdmin.value) {
    window.$message?.warning('只有管理员才能上传许可证');
    return false;
  }
  
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

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 租户配置操作手册 -->
    <NCard :bordered="false" size="small" class="operation-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="📋 租户配置操作手册">
          <div class="space-y-4 text-sm max-h-400px overflow-y-auto">
            <!-- 配置项说明 -->
            <NCard title="🏢 租户配置说明" size="small">
              <NList>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#2080f0">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">租户ID</div>
                      <div class="text-gray-600">系统自动生成的唯一标识，用于多租户隔离</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#18a058">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">租户名称</div>
                      <div class="text-gray-600">租户的显示名称，用于界面展示和识别</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#f0a020">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 11H7v6h2v-6zm4 0h-2v6h2v-6zm4 0h-2v6h2v-6zm2-7v2H5V4h3.5l1-1h5l1 1H19z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">上传方法</div>
                      <div class="text-gray-600">数据上传方式配置：FTP、HTTP、WebSocket等</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#d03050">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">许可证管理</div>
                      <div class="text-gray-600">控制系统功能授权和使用期限</div>
                    </div>
                  </NSpace>
                </NListItem>
              </NList>
            </NCard>

            <!-- 配置影响说明 -->
            <NCard title="⚙️ 配置项影响" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium text-orange-600">🔄 上传重试次数</div>
                    <div class="text-gray-600 mt-1">• 影响：数据上传失败时的重试频率</div>
                    <div class="text-gray-600">• 建议：网络稳定环境设置3-5次，不稳定环境可增加到10次</div>
                    <div class="text-gray-600">• 风险：过高会增加服务器负载，过低可能导致数据丢失</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-blue-600">💾 缓存最大数量</div>
                    <div class="text-gray-600 mt-1">• 影响：本地缓存的最大数据条数</div>
                    <div class="text-gray-600">• 建议：根据服务器内存设置，一般1000-10000条</div>
                    <div class="text-gray-600">• 风险：过高占用内存，过低影响查询性能</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-green-600">📤 启用续传功能</div>
                    <div class="text-gray-600 mt-1">• 影响：大文件上传中断后可继续传输</div>
                    <div class="text-gray-600">• 建议：大文件传输场景建议启用</div>
                    <div class="text-gray-600">• 风险：增加服务器存储开销</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-purple-600">🔐 许可证支持</div>
                    <div class="text-gray-600 mt-1">• 影响：控制租户可使用的系统功能模块</div>
                    <div class="text-gray-600">• 建议：根据客户付费等级设置对应权限</div>
                    <div class="text-gray-600">• 风险：关闭后相关功能将不可用</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 操作指南 -->
            <NCard title="📖 操作指南" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium">1. 新增租户配置</div>
                    <div class="text-gray-600 mt-1">点击"新增"按钮 → 填写租户基本信息 → 设置上传参数 → 配置许可证支持 → 保存</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">2. 编辑租户配置</div>
                    <div class="text-gray-600 mt-1">点击"编辑"按钮 → 修改相关配置项 → 注意许可证变更影响 → 保存更改</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">3. 许可证管理</div>
                    <div class="text-gray-600 mt-1">点击"许可证"按钮 → 查看当前状态 → 上传新许可证文件 → 验证生效</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">4. 配置删除</div>
                    <div class="text-gray-600 mt-1">谨慎操作：删除租户配置将影响该租户所有用户的系统访问</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 注意事项 -->
            <NAlert type="warning" title="⚠️ 重要提醒" show-icon class="mt-4">
              <div class="space-y-2">
                <div>• 修改上传方法后需要重启相关数据采集服务</div>
                <div>• 许可证过期会导致系统功能受限，请及时续期</div>
                <div>• 缓存配置变更建议在业务低峰期进行</div>
                <div>• 删除租户配置前请确保数据已备份</div>
              </div>
            </NAlert>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <CustomerConfigSearch v-model:model="searchParams" :org-units-name="orgUnitsName" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
:add-auth="isAdmin ? 't:customer:config:add' : ''"
        :delete-auth="isAdmin ? 't:customer:config:delete' : ''"
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
              :disabled="licenseUploading || !isAdmin"
            >
              <NButton :loading="licenseUploading" :disabled="!isAdmin" type="primary" size="small">
                {{ licenseUploading ? '上传中...' : (isAdmin ? '选择许可证文件' : '仅管理员可操作') }}
              </NButton>
            </NUpload>
            <div class="text-sm text-gray-500">
              <p>• 支持 .lic 格式的许可证文件</p>
              <p>• 上传新许可证后将自动重新验证</p>
              <p>• 建议在更新前备份当前配置</p>
              <p v-if="!isAdmin" class="text-orange-600">⚠️ 许可证上传功能仅限管理员使用</p>
            </div>
          </div>
        </NCard>
      </div>
    </NModal>
  </div>
</template>

