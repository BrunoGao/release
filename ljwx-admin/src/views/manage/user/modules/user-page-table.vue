<script setup lang="tsx">
import { NButton, NCard, NDataTable, NTag, useModal, NUpload, NUploadDragger, NP, NText, NIcon, NModal, NSpin } from 'naive-ui';
import { computed, h, reactive, ref, watch } from 'vue';
import { fetchCheckUserDeviceBinding, fetchDeleteUser, fetchGetUserList, fetchGetUserListByViewMode, fetchResetUserPassword, fetchBatchImportUsers, fetchBatchImportUsersDirect } from '@/service/api';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { transDeleteParams } from '@/utils/common';
import { useAuth } from '@/hooks/business/auth';
import { useButtonAuthDropdown } from '@/hooks/common/button-auth-dropdown';
import TableHeaderOperation from '@/components/advanced/table-header-operation.vue';
import UserResponsibilitiesSetting from '@/views/manage/user/modules/user-responsibilities-modal.vue';

import { useBoolean } from '~/packages/hooks';
import { useDict } from '@/hooks/business/dict';
import UserOperateDrawer from './user-operate-drawer.vue';
import UserSearch from './user-search.vue';
import UserViewModeSelector from './user-view-mode-selector.vue';
import { collectIdsFromItem } from './shared';

defineOptions({
  name: 'UserPageListTableEnhanced'
});

interface Props {
  orgUnits: Api.SystemManage.OrgUnitsTree;
}

const props = defineProps<Props>();

const orgIds = computed(() => collectIdsFromItem(props.orgUnits));

const modal = useModal();
const appStore = useAppStore();
const { hasAuth } = useAuth();
const { dictTag } = useDict();
const { bool: respModelVisible, setTrue: setRespModelVisible } = useBoolean();
const { bool: importModalVisible, setTrue: showImportModal, setFalse: hideImportModal } = useBoolean();

// 视图模式状态
const viewMode = ref<Api.SystemManage.ViewMode>('all');

// 批量导入状态
const importLoading = ref(false);
const importResult = ref<{
  success: any[];
  failed: any[];
  total: number;
} | null>(null);
const uploadedFile = ref<File | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// 根据视图模式动态获取API函数 #统一使用viewMode参数
const getApiFn = (mode: Api.SystemManage.ViewMode) => {
  return mode === 'all' ? fetchGetUserList : fetchGetUserListByViewMode;
};
type ButtonDropdownKey = 'delete' | 'resetPassword' | 'userResponsibilities';

// 根据视图模式和用户类型动态生成操作选项
const getOperationOptions = (user: Api.SystemManage.User) => {
  const baseOptions: CommonType.ButtonDropdown<ButtonDropdownKey, Api.SystemManage.User>[] = [
    {
      key: 'delete',
      label: $t('common.delete'),
      show: hasAuth('sys:user:delete') && (!user.isAdmin || hasAuth('sys:user:manage:admin')),
      handler: (_key, row) => handleDelete(row.id)
    },
    {
      key: 'resetPassword',
      label: $t('page.manage.user.resetPwd'),
      show: hasAuth('sys:user:resetPassword'),
      handler: (_key, row) => handleResetPassword(row.id)
    },
    {
      key: 'userResponsibilities',
      show: hasAuth('sys:user:responsibilities'),
      label: $t('page.manage.user.responsibilities'),
      handler: (_key, row) => handleResponsibilities(row.id)
    }
  ];

  return baseOptions;
};

const { renderDropdown } = useButtonAuthDropdown(getOperationOptions({} as Api.SystemManage.User));

// API参数
const apiParams = reactive({
  page: 1,
  pageSize: 10,
  userName: null,
  realName: null,
  email: null,
  orgIds: orgIds.value,
  viewMode: viewMode.value
});

// 根据视图模式动态生成列配置
const getDynamicColumns = (mode: Api.SystemManage.ViewMode) => {
  const baseColumns: any[] = [
    { type: 'selection', width: 40, align: 'center' },
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64
    },
    {
      key: 'userName',
      title: $t('page.manage.user.userName'),
      align: 'center',
      width: 100
    }
  ];

  // 在全部视图中显示用户类型列
  if (mode === 'all') {
    baseColumns.push({
      key: 'userType',
      title: '类型',
      align: 'center',
      width: 80,
      render: (row: Api.SystemManage.User) => {
        const isAdmin = row.isAdmin;
        return h(NTag, {
          type: isAdmin ? 'error' : 'success',
          size: 'small'
        }, {
          default: () => isAdmin ? '管理员' : '员工'
        });
      }
    });
  }

  // 管理员视图特殊列
  if (mode === 'admin') {
    baseColumns.push({
      key: 'adminRole',
      title: '管理权限',
      align: 'center',
      width: 120,
      render: (_row: Api.SystemManage.User) => {
        return h(NTag, {
          type: 'warning',
          size: 'small'
        }, {
          default: () => '系统管理员'
        });
      }
    });
  }

  // 添加其他通用列
  baseColumns.push(
    {
      key: 'userCardNumber',
      title: $t('page.manage.user.userCardNumber'),
      align: 'center',
      width: 100
    },
    {
      key: 'position',
      title: '职位',
      align: 'center',
      width: 100
    },
    {
      key: 'workingYears',
      title: '工龄',
      align: 'center',
      width: 100,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'gender',
      title: $t('page.manage.user.gender'),
      align: 'center',
      width: 100,
      render: (row: Api.SystemManage.User) => dictTag('gender', row.gender)
    },
    {
      key: 'phone',
      title: $t('page.manage.user.phone'),
      align: 'center',
      width: 120
    },
    {
      key: 'deviceSn',
      title: $t('page.manage.user.deviceSn'),
      align: 'center',
      width: 250,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'status',
      title: $t('page.manage.user.status'),
      align: 'center',
      width: 70,
      render: (row: Api.SystemManage.User) => dictTag('status', row.status)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      fixed: 'right',
      width: 150,
      render: (row: Api.SystemManage.User) => (
        <div class="flex-center gap-8px">
          {(hasAuth('sys:user:update') && (!row.isAdmin || hasAuth('sys:user:manage:admin'))) && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          )}
          <NButton type="primary" quaternary size="small" onClick={() => handleDeviceSubmitted(row.deviceSn)}>
            {$t('route.health_profile')}
          </NButton>
          {renderDropdown(row)}
        </div>
      )
    }
  );

  return baseColumns;
};

// 使用useTable hook #确保完整响应性
const tableConfig = reactive({
  apiFn: getApiFn(viewMode.value),
  apiParams,
  columns: () => getDynamicColumns(viewMode.value)
});

const { columns, columnChecks, data, getData, getDataByPage, loading, mobilePagination, searchParams, updateSearchParams, resetSearchParams } =
  useTable(tableConfig);



const {
  drawerVisible,
  operateType,
  editingId,
  editingData,
  handleAdd,
  handleEdit,
  handleId,
  checkedRowKeys,
  onBatchDeleted,
  onDeleted
} = useTableOperate(data, getData);

// 视图模式切换处理 #直接修改searchParams
const handleViewModeChange = async (mode: Api.SystemManage.ViewMode) => {
  viewMode.value = mode;

  // 直接修改searchParams
  searchParams.viewMode = mode;

  // 重新获取数据
  await getDataByPage();
};

function edit(id: string) {
  handleEdit(id);
}

async function handleDelete(id: string) {
  await performDeleteWithDeviceCheck([id], false);
}

async function handleBatchDelete() {
  await performDeleteWithDeviceCheck(checkedRowKeys.value, true);
}

/** 删除用户前检查设备绑定并显示确认框 #删除用户设备解绑检查 */
async function performDeleteWithDeviceCheck(userIds: string[], isBatch: boolean) {
  try {
    // 检查设备绑定状态
    const { error: checkError, data: bindingInfo } = await fetchCheckUserDeviceBinding(transDeleteParams(userIds));

    if (checkError) {
      window.$message?.error('检查设备绑定状态失败');
      return;
    }

    let content = isBatch ? `确认删除选中的 ${userIds.length} 个用户？` : $t('common.confirmDelete');

        // 如果有设备绑定，显示友好的提示信息 #设备解绑提示优化
    if (bindingInfo && bindingInfo.length > 0) {
      const deviceCount = bindingInfo.length;
      const deviceList = bindingInfo.map(info =>
        `  • ${info.userName} (设备号: ${info.deviceSn})`
      ).join('\n');

      content = `🔔 设备绑定提醒

检测到 ${deviceCount} 个用户绑定了手表设备：

${deviceList}

删除操作将自动执行：
  ✓ 解绑用户关联的手表设备
  ✓ 释放设备供其他用户重新绑定
  ✓ 记录设备解绑操作日志
  ✓ 删除用户账户信息

⚠️ 此操作不可撤销，确认继续删除吗？`;
    }

    modal.create({
      title: $t('common.delete'),
      content,
      preset: 'dialog',
      negativeText: $t('common.cancel'),
      positiveText: $t('common.confirm'),
      onPositiveClick: async () => {
        const { error, data: result } = await fetchDeleteUser(transDeleteParams(userIds));
        if (!error && result) {
          window.$message?.success(`成功删除 ${userIds.length} 个用户${bindingInfo?.length ? '并解绑设备' : ''}`);
          if (isBatch) {
            await onBatchDeleted();
          } else {
            await onDeleted();
          }
        }
      }
    });
  } catch (error) {
    window.$message?.error('操作失败，请重试');
    console.error('删除用户错误:', error);
  }
}

async function handleResetPassword(id: string) {
  modal.create({
    title: $t('page.manage.user.resetPwd'),
    content: $t('page.manage.user.confirmResetPwd'),
    preset: 'dialog',
    negativeText: $t('common.cancel'),
    positiveText: $t('common.confirm'),
    onPositiveClick: async () => {
      const { error, data: password } = await fetchResetUserPassword(id);
      if (!error) {
        modal.create({
          title: '',
          content: password,
          preset: 'dialog'
        });
      }
    }
  });
}

async function handleResponsibilities(id: string) {
  handleId(id);
  setRespModelVisible();
}

function handleDeviceSubmitted(deviceSn: string) {
  const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5002';
  window.open(`${bigscreenUrl}/personal?deviceSn=${deviceSn}`, '_blank');
}

// 下载模板
function downloadTemplate() {
  // 提供CSV格式模板下载
  const headers = ['姓名', '性别', '年龄', '工龄', '手机号码', '部门', '岗位', '设备序列号', '备注'];
  const sampleData = [
    ['张三', '男', '28', '3', '13800138000', '技术部', '软件工程师', 'SN001', '示例用户1'],
    ['李四', '女', '25', '2', '13900139000', '产品部', '产品经理', 'SN002', '示例用户2']
  ];
  
  const csvContent = [headers, ...sampleData]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n');
  
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', '用户批量导入模板.csv');
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  window.$message?.success('CSV模板下载完成！您也可以将此格式保存为Excel文件使用');
}

// 选择文件
function selectFile() {
  if (importLoading.value) return;
  fileInputRef.value?.click();
}

// 处理文件输入变化
function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) {
    uploadedFile.value = null;
    return;
  }
  
  console.log('选择的文件:', file.name, file.type, file.size);
  
  // 验证文件类型
  const validTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv',
    'application/csv'
  ];
  
  const fileName = file.name.toLowerCase();
  const isValidType = validTypes.includes(file.type) || 
                     fileName.endsWith('.xlsx') ||
                     fileName.endsWith('.xls') ||
                     fileName.endsWith('.csv');
  
  if (!isValidType) {
    window.$message?.error('请上传Excel文件(.xlsx, .xls)或CSV文件');
    uploadedFile.value = null;
    // 清空input值
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
    return;
  }
  
  uploadedFile.value = file;
  window.$message?.success('文件已选择，请点击提交按钮进行导入');
}

// 清除文件选择
function clearFileSelection() {
  uploadedFile.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
  window.$message?.info('文件已清除');
}

// 提交导入
async function submitImport() {
  if (!uploadedFile.value) {
    window.$message?.error('请先选择文件');
    return;
  }
  
  importLoading.value = true;
  importResult.value = null;
  
  try {
    console.log('准备发送请求:', {
      fileName: uploadedFile.value.name,
      fileSize: uploadedFile.value.size,
      fileType: uploadedFile.value.type,
      orgIds: orgIds.value,
      uploadedFileObject: uploadedFile.value
    });
    
    // 验证文件对象的完整性
    if (!uploadedFile.value.name || typeof uploadedFile.value.size !== 'number') {
      throw new Error('无效的文件对象');
    }
    
    // 首先尝试直接fetch方法
    console.log('尝试使用直接fetch方法...');
    const directResult = await fetchBatchImportUsersDirect(
      uploadedFile.value, 
      JSON.stringify(orgIds.value)
    );
    
    let result = directResult.data;
    let error = directResult.error;
    
    // 如果直接fetch失败，尝试原始方法
    if (error) {
      console.log('直接fetch失败，尝试原始API方法...');
      const originalResult = await fetchBatchImportUsers(
        uploadedFile.value, 
        JSON.stringify(orgIds.value)
      );
      result = originalResult.data;
      error = originalResult.error;
    }
    
    if (error) {
      console.error('API调用失败:', error);
      throw new Error(error.message || '调用接口失败');
    }
    
    console.log('服务器响应:', result);
    importResult.value = result;
    
    if (result && result.success && result.success.length > 0) {
      window.$message?.success(`成功导入 ${result.success.length} 个用户`);
      await getDataByPage();
    }
    
    if (result && result.failed && result.failed.length > 0) {
      window.$message?.warning(`${result.failed.length} 个用户导入失败，请查看详细信息`);
    }
    
    if (!result || (!result.success && !result.failed)) {
      window.$message?.warning('导入完成，但未收到详细结果');
    }
    
  } catch (error) {
    console.error('批量导入错误:', error);
    window.$message?.error(`批量导入失败: ${error.message}`);
  } finally {
    importLoading.value = false;
  }
}

// 显示批量导入弹窗
function handleBatchImport() {
  importResult.value = null;
  clearFileSelection();
  showImportModal();
}

watch(orgIds, () => {
  updateSearchParams({ orgIds: orgIds.value });
  apiParams.orgIds = orgIds.value;
  getDataByPage();
});

// 监听视图模式变化
watch(viewMode, () => {
  console.log('🔄 视图模式变化:', viewMode.value);
  handleViewModeChange(viewMode.value);
});
</script>

<template>
  <div class="h-full flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 视图模式选择器 -->
    <div class="flex items-center justify-between gap-4 p-4 bg-white rounded">
      <div class="flex items-center gap-4">
        <span class="text-sm font-medium">视图模式：</span>
        <UserViewModeSelector
          v-model:value="viewMode"
          :loading="loading"
        />
      </div>
      <div class="text-xs text-gray-500">
        当前显示：{{ viewMode === 'all' ? '全部用户' : viewMode === 'employee' ? '员工' : '管理员' }}
      </div>
    </div>

    <!-- 搜索区域 -->
    <UserSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />

    <!-- 表格区域 -->
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="sys:user:add"
        delete-auth="sys:user:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #suffix>
          <NButton
            v-if="hasAuth('sys:user:add')"
            size="small"
            ghost
            type="info"
            @click="handleBatchImport"
          >
            <template #icon>
              <icon-material-symbols:upload />
            </template>
            批量导入
          </NButton>
        </template>
      </TableHeaderOperation>
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
        :row-key="(row: any) => row.id"
        :pagination="mobilePagination"
      />
    </NCard>

    <!-- 弹窗组件 -->
    <UserOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      :org-ids="orgIds"
      @submitted="getDataByPage"
    />
    <UserResponsibilitiesSetting
      v-model:visible="respModelVisible"
      :user-id="editingId"
      @submitted="getDataByPage"
    />
    
    <!-- 批量导入弹窗 -->
    <NModal
      v-model:show="importModalVisible"
      :mask-closable="false"
      preset="dialog"
      title="批量导入用户"
      :style="{ width: '600px' }"
    >
      <div class="space-y-4">
        <!-- 操作提示 -->
        <div class="bg-blue-50 p-4 rounded-lg">
          <div class="flex items-center space-x-2 mb-2">
            <NIcon size="16" color="#1890ff">
              <icon-material-symbols:info />
            </NIcon>
            <span class="text-sm font-medium text-blue-800">导入说明</span>
          </div>
          <div class="text-xs text-blue-600 space-y-1">
            <p>1. 请先下载模板文件，按照模板格式填写用户信息</p>
            <p>2. 支持 Excel (.xlsx, .xls) 和 CSV 格式文件</p>
            <p>3. 必填字段：姓名、性别、年龄、工龄、手机号码、部门、岗位</p>
            <p>4. 部门和岗位必须在系统中存在且唯一</p>
          </div>
        </div>

        <!-- 下载模板 -->
        <div class="flex justify-center">
          <NButton type="primary" ghost @click="downloadTemplate">
            <template #icon>
              <icon-material-symbols:download />
            </template>
            下载导入模板
          </NButton>
        </div>

        <!-- 文件上传 -->
        <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <input
            ref="fileInputRef"
            type="file"
            accept=".xlsx,.xls,.csv"
            @change="handleFileInputChange"
            style="display: none"
            :disabled="importLoading"
          />
          <div @click="selectFile" class="cursor-pointer">
            <NIcon size="48" :depth="3" class="mb-2">
              <icon-material-symbols:upload />
            </NIcon>
            <div class="text-base mb-1">点击选择文件</div>
            <div class="text-xs text-gray-500">支持 Excel (.xlsx, .xls) 和 CSV 格式</div>
          </div>
        </div>

        <!-- 文件选择状态 -->
        <div v-if="uploadedFile" class="bg-green-50 p-3 rounded">
          <div class="flex items-center space-x-2">
            <NIcon size="16" color="#52c41a">
              <icon-material-symbols:check-circle />
            </NIcon>
            <span class="text-sm text-green-800">已选择文件: {{ uploadedFile.name }}</span>
          </div>
        </div>

        <!-- 提交按钮 -->
        <div class="flex justify-center space-x-3">
          <NButton
            v-if="uploadedFile && !importLoading"
            type="primary"
            @click="submitImport"
            :disabled="importLoading"
          >
            <template #icon>
              <icon-material-symbols:cloud-upload />
            </template>
            开始导入
          </NButton>
          <NButton
            v-if="uploadedFile"
            quaternary
            @click="clearFileSelection"
            :disabled="importLoading"
          >
            重新选择
          </NButton>
        </div>

        <!-- 当前状态显示 -->
        <div class="bg-gray-100 p-2 rounded text-xs">
          <div>上传状态: {{ uploadedFile ? '已选择文件' : '未选择文件' }}</div>
          <div v-if="uploadedFile">文件名: {{ uploadedFile.name }}</div>
          <div v-if="uploadedFile">文件类型: {{ uploadedFile.type }}</div>
          <div v-if="uploadedFile">文件大小: {{ Math.round(uploadedFile.size / 1024) }}KB</div>
          <div v-if="!uploadedFile">请选择要导入的文件</div>
        </div>

        <!-- 导入结果 -->
        <div v-if="importResult" class="space-y-3">
          <div class="font-medium text-gray-800">导入结果</div>
          
          <!-- 成功统计 -->
          <div class="bg-green-50 p-3 rounded">
            <div class="text-green-800 text-sm">
              ✅ 成功导入 {{ importResult.success.length }} 个用户
            </div>
          </div>
          
          <!-- 失败详情 -->
          <div v-if="importResult.failed.length > 0" class="bg-red-50 p-3 rounded">
            <div class="text-red-800 text-sm mb-2">
              ❌ 导入失败 {{ importResult.failed.length }} 个用户
            </div>
            <div class="max-h-32 overflow-y-auto">
              <div
                v-for="(item, index) in importResult.failed"
                :key="index"
                class="text-xs text-red-600 py-1 border-b border-red-200 last:border-b-0"
              >
                第{{ item.row }}行: {{ item.reason }}
              </div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="importLoading" class="text-center py-4">
          <NSpin size="small" />
          <span class="ml-2 text-sm text-gray-600">正在导入中...</span>
        </div>
      </div>

      <template #action>
        <NButton 
          @click="hideImportModal"
          :disabled="importLoading"
        >
          {{ importLoading ? '导入中...' : '关闭' }}
        </NButton>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.gap-8px {
  gap: 8px;
}
</style>
