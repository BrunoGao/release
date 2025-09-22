<script setup lang="tsx">
import { computed } from 'vue';
import { NButton, NPopconfirm, NTag, NDropdown, NSpace, NDivider } from 'naive-ui';
import { useBoolean } from '@sa/hooks';
import { fetchDeleteRole, fetchGetRoleList } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { useAuth } from '@/hooks/business/auth';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';
import SvgIcon from '@/components/custom/svg-icon.vue';
import RoleOperateDrawer from './modules/role-operate-drawer.vue';
import RoleSearch from './modules/role-search.vue';
import MenuAuthModal from './modules/menu-auth-modal.vue';
import ButtonAuthModal from './modules/button-auth-modal.vue';

const appStore = useAppStore();
const authStore = useAuthStore();

const { bool: menuModalVisible, setTrue: openMenuModal } = useBoolean();

const { bool: buttonModalVisible, setTrue: openButtonModal } = useBoolean();

const { hasAuth } = useAuth();

const { dictTag } = useDict();

// 判断是否是超级管理员（admin用户，可以管理所有租户的角色）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 当前用户的租户ID
const currentCustomerId = authStore.userInfo?.customerId || null;

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetRoleList,
  apiParams: {
    page: 1,
    pageSize: 20,
    // if you want to use the searchParams in Form, you need to define the following properties, and the value is null
    // the value can not be undefined, otherwise the property in Form will not be reactive
    status: null,
    roleName: null,
    roleCode: null,
    // \u975e admin \u7528\u6237\u53ea\u67e5\u770b\u81ea\u5df1\u79df\u6237\u7684\u89d2\u8272
    customerId: isAdmin.value ? null : currentCustomerId
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'roleName',
      title: $t('page.manage.role.roleName'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'roleCode',
      title: $t('page.manage.role.roleCode'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'isAdmin',
      title: $t('page.manage.role.isAdmin'),
      align: 'center',
      width: 100,
      render: row => (
        <NTag type={row.isAdmin ? 'error' : 'success'} size="small">
          {row.isAdmin ? $t('page.manage.role.adminRole') : $t('page.manage.role.normalRole')}
        </NTag>
      )
    },
    {
      key: 'adminLevel',
      title: $t('page.manage.role.adminLevel'),
      align: 'center',
      width: 120,
      render: row => {
        if (!row.isAdmin) {
          return '-';
        }
        const levelMap = {
          0: { text: '超级管理员', type: 'error' },
          1: { text: '租户管理员', type: 'warning' },
          2: { text: '部门管理员', type: 'info' }
        };
        const level = levelMap[row.adminLevel] || { text: '未知', type: 'default' };
        return (
          <NTag type={level.type} size="small">
            {level.text}
          </NTag>
        );
      }
    },
    {
      key: 'status',
      title: $t('page.manage.role.status'),
      align: 'center',
      width: 100,
      render: row => dictTag('status', row.status)
    },
    {
      key: 'description',
      title: $t('page.manage.role.description'),
      align: 'center',
      minWidth: 120
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      render: row => {
        const permissionOptions = getPermissionMenuOptions(row);
        const operateOptions = getOperateMenuOptions(row);
        
        return (
          <NSpace size="small" justify="center">
            {/* 权限管理下拉菜单 */}
            {permissionOptions.length > 0 && (
              <NDropdown
                trigger="click"
                options={permissionOptions}
                size="small"
                placement="bottom-start"
              >
                <NButton
                  type="primary"
                  size="small"
                  class="permission-dropdown-btn"
                  renderIcon={() => <SvgIcon icon="material-symbols:security" class="text-14px" />}
                >
                  权限管理
                  <SvgIcon icon="material-symbols:arrow-drop-down" class="text-12px ml-4px" />
                </NButton>
              </NDropdown>
            )}
            
            {/* 操作下拉菜单 */}
            {operateOptions.length > 0 && (
              <NDropdown
                trigger="click"
                options={operateOptions}
                size="small"
                placement="bottom-start"
              >
                <NButton
                  type="default"
                  size="small" 
                  class="operate-dropdown-btn"
                  renderIcon={() => <SvgIcon icon="material-symbols:more-vert" class="text-14px" />}
                >
                  更多
                  <SvgIcon icon="material-symbols:arrow-drop-down" class="text-12px ml-4px" />
                </NButton>
              </NDropdown>
            )}
          </NSpace>
        );
      }
    }
  ]
});

const { drawerVisible, operateType, editingId, editingData, handleId, handleAdd, handleEdit, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, getData);

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteRole(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    onBatchDeleted();
  }
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteRole(transDeleteParams([id]));
  if (!error && result) {
    onDeleted();
  }
}

function edit(id: string) {
  handleEdit(id);
}

function handleMenuAuth(id: string) {
  handleId(id);
  openMenuModal();
}

function handleButtonAuth(id: string) {
  handleId(id);
  openButtonModal();
}

// 权限管理下拉菜单选项
function getPermissionMenuOptions(row: any) {
  const options = [];
  
  if (hasAuth('sys:role:menu:add')) {
    options.push({
      label: $t('page.manage.role.menuAuth'),
      key: 'menu',
      icon: () => <SvgIcon icon="material-symbols:menu-book" class="text-16px text-blue-500" />,
      props: {
        onClick: () => handleMenuAuth(row.id)
      }
    });
  }
  
  if (hasAuth('sys:role:permission:add')) {
    options.push({
      label: $t('page.manage.role.buttonAuth'),
      key: 'button',
      icon: () => <SvgIcon icon="material-symbols:smart-button" class="text-16px text-orange-500" />,
      props: {
        onClick: () => handleButtonAuth(row.id)
      }
    });
  }
  
  return options;
}

// 操作下拉菜单选项
function getOperateMenuOptions(row: any) {
  const options = [];
  
  if (hasAuth('sys:role:update')) {
    options.push({
      label: $t('common.edit'),
      key: 'edit',
      icon: () => <SvgIcon icon="material-symbols:edit" class="text-16px text-blue-500" />,
      props: {
        onClick: () => edit(row.id)
      }
    });
  }
  
  if (hasAuth('sys:role:delete')) {
    options.push({
      type: 'divider',
      key: 'divider'
    });
    options.push({
      label: $t('common.delete'),
      key: 'delete',
      icon: () => <SvgIcon icon="material-symbols:delete" class="text-16px text-red-500" />,
      props: {
        onClick: () => handleDelete(row.id)
      }
    });
  }
  
  return options;
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <RoleSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="sys:role:add"
        delete-auth="sys:role:delete"
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
      <RoleOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :is-admin="isAdmin"
        :current-customer-id="currentCustomerId"
        @submitted="getDataByPage"
      />
      <MenuAuthModal v-model:visible="menuModalVisible" :role-id="editingId" />
      <ButtonAuthModal v-model:visible="buttonModalVisible" :role-id="editingId" />
    </NCard>
  </div>
</template>

<style scoped>
/* 下拉按钮样式 */
.permission-dropdown-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: 1px solid #3b82f6;
  color: white;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
  min-width: 90px;
}

.permission-dropdown-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}

.operate-dropdown-btn {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #cbd5e1;
  color: #475569;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(71, 85, 105, 0.1);
  min-width: 70px;
}

.operate-dropdown-btn:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  border-color: #94a3b8;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(71, 85, 105, 0.15);
}

/* 图标样式优化 */
.permission-dropdown-btn :deep(.n-button__icon),
.operate-dropdown-btn :deep(.n-button__icon) {
  margin-right: 4px;
}

/* 下拉菜单样式优化 */
:deep(.n-dropdown-menu) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

:deep(.n-dropdown-option) {
  padding: 10px 16px;
  transition: all 0.2s ease;
}

:deep(.n-dropdown-option:hover) {
  background-color: #f8fafc;
}

:deep(.n-dropdown-option .n-dropdown-option__icon) {
  margin-right: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .permission-dropdown-btn,
  .operate-dropdown-btn {
    min-width: 60px;
    font-size: 12px;
    padding: 0 8px;
  }
  
  .permission-dropdown-btn span,
  .operate-dropdown-btn span {
    display: none;
  }
  
  .permission-dropdown-btn :deep(.n-button__icon),
  .operate-dropdown-btn :deep(.n-button__icon) {
    margin-right: 0;
  }
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

/* 角色标签样式优化 */
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
</style>
