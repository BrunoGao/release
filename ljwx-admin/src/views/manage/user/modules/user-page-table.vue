<script setup lang="tsx">
import { NButton, NCard, NDataTable, NTag, useModal } from 'naive-ui';
import { computed, h, reactive, ref, watch } from 'vue';
import { fetchCheckUserDeviceBinding, fetchDeleteUser, fetchGetUserList, fetchGetUserListByViewMode, fetchResetUserPassword } from '@/service/api';
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

// 视图模式状态
const viewMode = ref<Api.SystemManage.ViewMode>('all');

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
