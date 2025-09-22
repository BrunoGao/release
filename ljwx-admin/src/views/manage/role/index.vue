<script setup lang="tsx">
import { computed } from 'vue';
import { NButton, NPopconfirm, NTag } from 'naive-ui';
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
      width: 300,
      render: row => (
        <div class="flex-center gap-12px">
          {hasAuth('sys:role:menu:add') && (
            <NButton
              type="info"
              secondary
              size="small"
              class="permission-btn menu-permission-btn"
              onClick={() => handleMenuAuth(row.id)}
              renderIcon={() => <SvgIcon icon="material-symbols:menu-book" class="text-14px" />}
            >
              {$t('page.manage.role.menuAuth')}
            </NButton>
          )}
          {hasAuth('sys:role:permission:add') && (
            <NButton
              type="warning"
              secondary
              size="small"
              class="permission-btn button-permission-btn"
              onClick={() => handleButtonAuth(row.id)}
              renderIcon={() => <SvgIcon icon="material-symbols:smart-button" class="text-14px" />}
            >
              {$t('page.manage.role.buttonAuth')}
            </NButton>
          )}
          {hasAuth('sys:role:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('sys:role:delete') && (
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
.permission-btn {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 100px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.menu-permission-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: 1px solid #3b82f6;
  color: white;
}

.menu-permission-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.button-permission-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: 1px solid #f59e0b;
  color: white;
}

.button-permission-btn:hover {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
}

.permission-btn :deep(.n-button__icon) {
  margin-right: 6px;
}
</style>
