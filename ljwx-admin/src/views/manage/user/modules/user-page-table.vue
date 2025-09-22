<script setup lang="tsx">
import { NButton, NCard, NDataTable, NIcon, NModal, NP, NSpin, NTag, NText, NUpload, NUploadDragger, useModal, NDropdown, NSpace, NDivider, NPopconfirm } from 'naive-ui';
import { computed, h, reactive, ref, watch } from 'vue';
import SvgIcon from '@/components/custom/svg-icon.vue';
import {
  fetchBatchImportUsers,
  fetchBatchImportUsersDirect,
  fetchCheckUserDeviceBinding,
  fetchDeleteUser,
  fetchGetUserList,
  fetchGetUserListByViewMode,
  fetchResetUserPassword
} from '@/service/api';
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

// 管理操作下拉菜单选项
function getManageMenuOptions(row: Api.SystemManage.User) {
  if (!row || !row.id) {
    console.warn('用户行数据无效:', row);
    return [];
  }
  
  const options: any[] = [];
  
  try {
    // 编辑操作
    if (hasAuth('sys:user:update') && (!row.isAdmin || hasAuth('sys:user:manage:admin'))) {
      options.push({
        label: '编辑',
        key: 'edit',
        icon: renderIcon('material-symbols:edit')
      });
    }
    
    if (hasAuth('sys:user:resetPassword')) {
      options.push({
        label: '重置密码',
        key: 'resetPassword',
        icon: renderIcon('material-symbols:lock-reset')
      });
    }
    
    if (hasAuth('sys:user:responsibilities')) {
      options.push({
        label: '权责设置',
        key: 'responsibilities',
        icon: renderIcon('material-symbols:admin-panel-settings')
      });
    }
    
    // 添加分隔线（如果有删除权限）
    if (hasAuth('sys:user:delete') && (!row.isAdmin || hasAuth('sys:user:manage:admin')) && options.length > 0) {
      options.push({
        type: 'divider',
        key: 'divider'
      });
    }
    
    // 删除操作
    if (hasAuth('sys:user:delete') && (!row.isAdmin || hasAuth('sys:user:manage:admin'))) {
      options.push({
        label: '删除',
        key: 'delete',
        icon: renderIcon('material-symbols:delete')
      });
    }
    
    console.log('生成的管理选项:', options, '用户:', row.userName);
  } catch (error) {
    console.error('生成管理菜单选项时出错:', error);
  }
  
  return options;
}

// 图标渲染辅助函数
function renderIcon(icon: string) {
  return () => h(SvgIcon, { icon, class: 'text-16px' });
}

// 移除危险操作下拉菜单选项（已整合到管理菜单中）

// 移除旧的下拉菜单逻辑

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
        return h(
          NTag,
          {
            type: isAdmin ? 'error' : 'success',
            size: 'small'
          },
          {
            default: () => (isAdmin ? '管理员' : '员工')
          }
        );
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
        return h(
          NTag,
          {
            type: 'warning',
            size: 'small'
          },
          {
            default: () => '系统管理员'
          }
        );
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
      width: 200,
      render: (row: Api.SystemManage.User) => {
        try {
          if (!row) {
            console.warn('用户行数据为空');
            return h('div', '数据错误');
          }
          
          const manageOptions = getManageMenuOptions(row);
          
          return h(NSpace, { 
            size: 'small', 
            justify: 'center', 
            wrap: false 
          }, {
            default: () => [
              // 健康档案按钮
              h(NButton, {
                type: 'success',
                size: 'small',
                class: 'user-action-btn health-btn',
                onClick: () => handleDeviceSubmitted(row.deviceSn || ''),
                renderIcon: () => h(SvgIcon, { icon: 'material-symbols:health-and-safety', class: 'text-14px' })
              }, {
                default: () => '健康档案'
              }),
              
              // 管理操作下拉菜单（包含编辑、重置密码、权责设置、删除）
              manageOptions.length > 0 ? h(NDropdown, {
                trigger: 'click',
                options: manageOptions,
                size: 'small',
                placement: 'bottom-start',
                showArrow: false,
                onSelect: (key: string) => {
                  console.log('下拉菜单选择:', key, '用户ID:', row.id);
                  switch (key) {
                    case 'edit':
                      edit(row.id);
                      break;
                    case 'resetPassword':
                      handleResetPassword(row.id);
                      break;
                    case 'responsibilities':
                      handleResponsibilities(row.id);
                      break;
                    case 'delete':
                      handleDelete(row.id);
                      break;
                    default:
                      console.warn('未知的菜单选项:', key);
                  }
                }
              }, {
                default: () => h(NButton, {
                  type: 'primary',
                  size: 'small',
                  class: 'user-action-btn manage-btn',
                  renderIcon: () => h(SvgIcon, { icon: 'material-symbols:settings', class: 'text-14px' })
                }, {
                  default: () => [
                    '管理',
                    h(SvgIcon, { icon: 'material-symbols:arrow-drop-down', class: 'text-12px ml-4px' })
                  ]
                })
              }) : null
            ].filter(Boolean)
          });
        } catch (error) {
          console.error('渲染操作列时出错:', error);
          return h('div', '渲染错误');
        }
      }
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

const { drawerVisible, operateType, editingId, editingData, handleAdd, handleEdit, handleId, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, getData);

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
      const deviceList = bindingInfo.map(info => `  • ${info.userName} (设备号: ${info.deviceSn})`).join('\n');

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

  const csvContent = [headers, ...sampleData].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

  const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' });
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
  const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv', 'application/csv'];

  const fileName = file.name.toLowerCase();
  const isValidType = validTypes.includes(file.type) || fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileName.endsWith('.csv');

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
    const directResult = await fetchBatchImportUsersDirect(uploadedFile.value, JSON.stringify(orgIds.value));

    let result = directResult.data;
    let error = directResult.error;

    // 如果直接fetch失败，尝试原始方法
    if (error) {
      console.log('直接fetch失败，尝试原始API方法...');
      const originalResult = await fetchBatchImportUsers(uploadedFile.value, JSON.stringify(orgIds.value));
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
    <div class="flex items-center justify-between gap-4 rounded bg-white p-4">
      <div class="flex items-center gap-4">
        <span class="text-sm font-medium">视图模式：</span>
        <UserViewModeSelector v-model:value="viewMode" :loading="loading" />
      </div>
      <div class="text-xs text-gray-500">当前显示：{{ viewMode === 'all' ? '全部用户' : viewMode === 'employee' ? '员工' : '管理员' }}</div>
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
        <!-- 隐藏批量导入按钮 -->
        <template #suffix>
          <!-- 批量导入功能已隐藏 -->
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
    <UserResponsibilitiesSetting v-model:visible="respModelVisible" :user-id="editingId" @submitted="getDataByPage" />

    <!-- 批量导入弹窗 -->
    <NModal v-model:show="importModalVisible" :mask-closable="false" preset="dialog" title="批量导入用户" :style="{ width: '600px' }">
      <div class="space-y-4">
        <!-- 操作提示 -->
        <div class="rounded-lg bg-blue-50 p-4">
          <div class="mb-2 flex items-center space-x-2">
            <NIcon size="16" color="#1890ff">
              <i class="i-material-symbols:info"></i>
            </NIcon>
            <span class="text-sm text-blue-800 font-medium">导入说明</span>
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
              <i class="i-material-symbols:download"></i>
            </template>
            下载导入模板
          </NButton>
        </div>

        <!-- 文件上传 -->
        <div class="border-2 border-gray-300 rounded-lg border-dashed p-6 text-center">
          <input
            ref="fileInputRef"
            type="file"
            accept=".xlsx,.xls,.csv"
            style="display: none"
            :disabled="importLoading"
            @change="handleFileInputChange"
          />
          <div class="cursor-pointer" @click="selectFile">
            <NIcon size="48" :depth="3" class="mb-2">
              <i class="i-material-symbols:upload"></i>
            </NIcon>
            <div class="mb-1 text-base">点击选择文件</div>
            <div class="text-xs text-gray-500">支持 Excel (.xlsx, .xls) 和 CSV 格式</div>
          </div>
        </div>

        <!-- 文件选择状态 -->
        <div v-if="uploadedFile" class="rounded bg-green-50 p-3">
          <div class="flex items-center space-x-2">
            <NIcon size="16" color="#52c41a">
              <i class="i-material-symbols:check-circle"></i>
            </NIcon>
            <span class="text-sm text-green-800">已选择文件: {{ uploadedFile.name }}</span>
          </div>
        </div>

        <!-- 提交按钮 -->
        <div class="flex justify-center space-x-3">
          <NButton v-if="uploadedFile && !importLoading" type="primary" :disabled="importLoading" @click="submitImport">
            <template #icon>
              <i class="i-material-symbols:cloud-upload"></i>
            </template>
            开始导入
          </NButton>
          <NButton v-if="uploadedFile" quaternary :disabled="importLoading" @click="clearFileSelection">重新选择</NButton>
        </div>

        <!-- 当前状态显示 -->
        <div class="rounded bg-gray-100 p-2 text-xs">
          <div>上传状态: {{ uploadedFile ? '已选择文件' : '未选择文件' }}</div>
          <div v-if="uploadedFile">文件名: {{ uploadedFile.name }}</div>
          <div v-if="uploadedFile">文件类型: {{ uploadedFile.type }}</div>
          <div v-if="uploadedFile">文件大小: {{ Math.round(uploadedFile.size / 1024) }}KB</div>
          <div v-if="!uploadedFile">请选择要导入的文件</div>
        </div>

        <!-- 导入结果 -->
        <div v-if="importResult" class="space-y-3">
          <div class="text-gray-800 font-medium">导入结果</div>

          <!-- 成功统计 -->
          <div class="rounded bg-green-50 p-3">
            <div class="text-sm text-green-800">✅ 成功导入 {{ importResult.success.length }} 个用户</div>
          </div>

          <!-- 失败详情 -->
          <div v-if="importResult.failed.length > 0" class="rounded bg-red-50 p-3">
            <div class="mb-2 text-sm text-red-800">❌ 导入失败 {{ importResult.failed.length }} 个用户</div>
            <div class="max-h-32 overflow-y-auto">
              <div
                v-for="(item, index) in importResult.failed"
                :key="index"
                class="border-b border-red-200 py-1 text-xs text-red-600 last:border-b-0"
              >
                第{{ item.row }}行: {{ item.reason }}
              </div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="importLoading" class="py-4 text-center">
          <NSpin size="small" />
          <span class="ml-2 text-sm text-gray-600">正在导入中...</span>
        </div>
      </div>

      <template #action>
        <NButton :disabled="importLoading" @click="hideImportModal">
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

/* 用户操作按钮通用样式 */
.user-action-btn {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 68px;
  height: 28px;
  font-size: 12px;
}

.user-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

/* 移除已不使用的编辑和危险操作按钮样式 */

/* 健康档案按钮样式 */
.health-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: 1px solid #10b981;
  color: white;
}

.health-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

/* 管理按钮样式（调整为蓝色系） */
.manage-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: 1px solid #3b82f6;
  color: white;
}

.manage-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

/* 移除危险操作按钮样式（已不使用） */

/* 按钮图标样式 */
.user-action-btn :deep(.n-button__icon) {
  margin-right: 4px;
}

/* 下拉菜单样式优化 */
:deep(.n-dropdown-menu) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
  min-width: 140px;
}

:deep(.n-dropdown-option) {
  padding: 12px 16px;
  transition: all 0.2s ease;
  border-radius: 0;
}

:deep(.n-dropdown-option:hover) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  transform: translateX(4px);
}

:deep(.n-dropdown-option .n-dropdown-option__icon) {
  margin-right: 8px;
}

/* 表格整体优化 */
:deep(.n-data-table-th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background-color: #f8fafc;
}

/* 用户类型标签样式优化 */
:deep(.n-tag) {
  border-radius: 6px;
  font-weight: 500;
  padding: 4px 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 卡片样式优化 */
.card-wrapper {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}

.card-wrapper :deep(.n-card__content) {
  padding: 20px;
}

/* 视图模式选择器美化 */
.view-mode-selector {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .user-action-btn {
    min-width: 60px;
    padding: 0 8px;
  }
  
  .user-action-btn span {
    display: none;
  }
  
  .user-action-btn :deep(.n-button__icon) {
    margin-right: 0;
  }
}

@media (max-width: 768px) {
  .user-action-btn {
    min-width: 32px;
    width: 32px;
    height: 32px;
    padding: 0;
    border-radius: 50%;
  }
  
  .manage-btn .n-button__content span:last-child {
    display: none;
  }
}

/* 操作列固定优化 */
:deep(.n-data-table-td:last-child) {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
}

/* 批量选择优化 */
:deep(.n-data-table-th:first-child),
:deep(.n-data-table-td:first-child) {
  background: rgba(248, 250, 252, 0.95);
  backdrop-filter: blur(8px);
}

/* 加载状态优化 */
:deep(.n-data-table--loading) {
  position: relative;
}

:deep(.n-data-table--loading::after) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
  z-index: 1;
}
</style>
