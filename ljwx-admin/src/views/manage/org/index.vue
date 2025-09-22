<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, ref } from 'vue';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useCustomer } from '@/hooks/business/customer';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { fetchDeleteOrgUnits, fetchGetOrgUnitsPageList, fetchOrgUnitsDeletePrecheck, fetchOrgUnitsCascadeDelete } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { transDeleteParams } from '@/utils/common';
import { useDict } from '@/hooks/business/dict';
import OrgUnitsOperateDrawer, { type OperateType } from './modules/org-units-operate-drawer.vue';
import OrgUnitsSearch from './modules/org-units-search.vue';
import DeleteConfirmDialog from '@/components/business/DeleteConfirmDialog.vue';

defineOptions({
  name: 'OrgUnitsPage'
});

const appStore = useAppStore();

const { hasAuth } = useAuth();

const authStore = useAuthStore();
const { currentCustomerId: globalCustomerId, currentCustomer } = useCustomer();

const { dictTag } = useDict();

// 基于全局选择的租户判断权限
// 所有用户在选择租户后都只能管理该租户下的部门
const currentCustomerId = computed(() => {
  const id = globalCustomerId.value || '0';
  console.log('[Debug] currentCustomerId from globalCustomerId:', id, 'globalCustomerId:', globalCustomerId.value);
  return id;
});

// 判断是否可以管理当前租户的部门（所有用户都可以管理选择的租户下的部门）
const canManageDepartments = computed(() => {
  const canManage = currentCustomerId.value && currentCustomerId.value !== '0';
  console.log('[Debug] canManageDepartments:', canManage, 'currentCustomerId:', currentCustomerId.value);
  return canManage; // 只要选择了具体租户就可以管理部门
});

// 租户信息显示
const currentTenantInfo = computed(() => {
  return {
    customerId: currentCustomerId.value,
    customerName: currentCustomer.value?.name || '未选择租户'
  };
});

const operateType = ref<OperateType>('add');

const editingData: Ref<Api.SystemManage.OrgUnits | null> = ref(null);

// 删除确认对话框相关状态
const deleteConfirmVisible = ref(false);
const deletePreCheckData = ref<Api.SystemManage.DepartmentDeletePreCheck | null>(null);
const deletePreCheckLoading = ref(false);
const pendingDeleteIds = ref<string[]>([]);

// 获取当前租户ID（由TenantInfo组件控制）
const customerId = computed(() => currentCustomerId.value);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetOrgUnitsPageList,
  apiParams: {
    page: 1,
    pageSize: 20,
    name: null,
    status: null
    // customerId 将由请求拦截器自动添加
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
      key: 'name',
      title: $t('page.manage.orgUnits.dept.name'),
      align: 'center',
      width: 150,
      minWidth: 150,
      render: row => row.name || '-'
    },
    {
      key: 'code',
      title: $t('page.manage.orgUnits.dept.code'),
      align: 'center',
      width: 100,
      minWidth: 100,
      render: row => row.code || '-'
    },
    {
      key: 'abbr',
      title: $t('page.manage.orgUnits.dept.abbr'),
      align: 'center',
      width: 100,
      minWidth: 100,
      render: row => row.abbr || '-'
    },
    {
      key: 'description',
      title: $t('page.manage.orgUnits.dept.description'),
      align: 'center',
      width: 120,
      minWidth: 120,
      render: row => row.description || '-'
    },
    {
      key: 'sort',
      title: $t('page.manage.orgUnits.sort'),
      align: 'center',
      width: 50,
      minWidth: 50,
      render: row => row.sort || '-'
    },
    {
      key: 'status',
      title: $t('page.manage.orgUnits.dept.status'),
      align: 'center',
      width: 60,
      minWidth: 60,
      render: row => dictTag('status', row.status)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 40,
      minWidth: 240,
      render: row => (
        <div class="flex-center gap-8px">
          <NButton type="primary" quaternary size="small" onClick={() => handleAddChildOrgUnits(row)}>
            {$t('page.manage.orgUnits.addChildDepartment')}
          </NButton>
          <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
            {$t('common.edit')}
          </NButton>
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
        </div>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  // 只能添加部门，检查是否选择了租户
  if (!canManageDepartments.value) {
    window.$message?.warning('请先选择租户后再添加部门');
    return;
  }
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.SystemManage.OrgUnits) {
  if (!canManageDepartments.value) {
    window.$message?.warning('请先选择租户后再编辑部门');
    return;
  }
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  await handleDeleteWithPrecheck([id]);
}

async function handleBatchDelete() {
  await handleDeleteWithPrecheck(checkedRowKeys.value);
}

async function handleDeleteWithPrecheck(ids: string[]) {
  try {
    // 设置待删除的ID列表
    pendingDeleteIds.value = ids;
    
    // 显示对话框并开始预检查
    deleteConfirmVisible.value = true;
    deletePreCheckLoading.value = true;
    deletePreCheckData.value = null;
    
    // 执行删除预检查
    const { error, data } = await fetchOrgUnitsDeletePrecheck(transDeleteParams(ids));
    
    if (!error && data) {
      deletePreCheckData.value = data;
    } else {
      window.$message?.error('删除预检查失败，请稍后重试');
      deleteConfirmVisible.value = false;
    }
  } catch (err) {
    console.error('删除预检查异常:', err);
    window.$message?.error('删除预检查异常');
    deleteConfirmVisible.value = false;
  } finally {
    deletePreCheckLoading.value = false;
  }
}

async function handleDeleteConfirm() {
  try {
    const ids = pendingDeleteIds.value;
    if (ids.length === 0) return;
    
    // 根据预检查结果决定使用哪种删除方式
    let deleteResult;
    if (deletePreCheckData.value?.canSafeDelete) {
      // 安全删除：使用常规删除API
      const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams(ids));
      deleteResult = { error, result };
    } else {
      // 级联删除：使用级联删除API
      const { error, data: result } = await fetchOrgUnitsCascadeDelete(transDeleteParams(ids));
      deleteResult = { error, result };
    }
    
    if (!deleteResult.error && deleteResult.result) {
      window.$message?.success(
        deletePreCheckData.value?.canSafeDelete 
          ? '删除成功' 
          : '级联删除成功，相关用户和设备已被处理'
      );
      
      // 根据删除类型调用相应的刷新函数
      if (ids.length === 1) {
        await onDeleted();
      } else {
        await onBatchDeleted();
      }
    } else {
      window.$message?.error('删除失败，请稍后重试');
    }
  } catch (err) {
    console.error('删除操作异常:', err);
    window.$message?.error('删除操作异常');
  } finally {
    // 重置状态
    deleteConfirmVisible.value = false;
    deletePreCheckData.value = null;
    pendingDeleteIds.value = [];
  }
}

function handleDeleteCancel() {
  // 重置状态
  deleteConfirmVisible.value = false;
  deletePreCheckData.value = null;
  pendingDeleteIds.value = [];
}

async function handleAddChildOrgUnits(item: Api.SystemManage.OrgUnits) {
  if (!canManageDepartments.value) {
    window.$message?.warning('请先选择租户后再添加子部门');
    return;
  }
  operateType.value = 'addChild';
  editingData.value = { ...item };
  openDrawer();
}
</script>

<template>
  <div class="org-management-beautiful">
    <!-- 美化的页面头部 -->
    <div class="page-header-beautiful">
      <NCard :bordered="false" class="header-card">
        <div class="header-content">
          <div class="header-left">
            <div class="header-icon">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7V10C2 16 6 20.5 12 22C18 20.5 22 16 22 10V7L12 2Z" stroke="currentColor" stroke-width="2" fill="url(#gradient)" />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color: #667eea; stop-opacity: 1" />
                    <stop offset="100%" style="stop-color: #764ba2; stop-opacity: 1" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="header-text">
              <h1 class="header-title">部门管理</h1>
              <p class="header-subtitle">
                {{ currentCustomerId > 0 ? `当前租户：${currentTenantInfo.customerName} (ID: ${currentCustomerId})` : '请先在右上角选择租户，然后管理该租户下的部门' }}
              </p>
            </div>
          </div>
          <div class="header-right">
            <div class="stats-mini">
              <div class="stat-item">
                <span class="stat-number">{{ data?.length || 0 }}</span>
                <span class="stat-label">部门数量</span>
              </div>
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <OrgUnitsSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    </div>

    <!-- 表格区域 -->
    <div class="table-section">
      <NCard :bordered="false" class="table-card">
        <div class="table-header">
          <TableHeaderOperation
            v-model:columns="columnChecks"
            :checked-row-keys="checkedRowKeys"
            :loading="loading"
            add-auth="sys:org:units:add"
            delete-auth="sys:org:units:delete"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @refresh="getData"
          />
        </div>

        <div class="table-container">
          <!-- 数据表格 -->
          <NDataTable
            v-if="data && data.length > 0"
            v-model:checked-row-keys="checkedRowKeys"
            striped
            size="small"
            class="beautiful-table"
            :data="data"
            :scroll-x="962"
            :columns="columns"
            :loading="loading"
            :single-line="false"
            :row-key="row => row.id"
          />
          
          <!-- 空状态提示 -->
          <div v-else-if="!loading && canManageDepartments" class="empty-state">
            <div class="empty-content">
              <div class="empty-icon">
                <svg viewBox="0 0 64 64" class="icon">
                  <path d="M32 8C18.7 8 8 18.7 8 32s10.7 24 24 24 24-10.7 24-24S45.3 8 32 8zM32 52c-11 0-20-9-20-20s9-20 20-20 20 9 20 20-9 20-20 20z" fill="#e2e8f0" />
                  <path d="M32 20c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2s2-.9 2-2v-8c0-1.1-.9-2-2-2zM32 36c-1.1 0-2 .9-2 2v2c0 1.1.9 2 2 2s2-.9 2-2v-2c0-1.1-.9-2-2-2z" fill="#94a3b8" />
                </svg>
              </div>
              <h3 class="empty-title">该租户下暂无部门</h3>
              <p class="empty-description">
                当前租户：{{ currentTenantInfo.customerName }}<br>
                您可以为该租户创建第一个部门
              </p>
              <NButton 
                type="primary" 
                size="large" 
                @click="handleAdd"
                class="add-department-btn"
              >
                <template #icon>
                  <i class="i-material-symbols:add"></i>
                </template>
                添加部门
              </NButton>
            </div>
          </div>
          
          <!-- 未选择租户的提示 -->
          <div v-else-if="!loading && !canManageDepartments" class="no-tenant-state">
            <div class="empty-content">
              <div class="empty-icon">
                <svg viewBox="0 0 64 64" class="icon">
                  <path d="M32 8l8 8H56v32H8V16h16l8-8z" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linejoin="round"/>
                  <path d="M24 28h16M24 36h16M24 44h12" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3 class="empty-title">请选择租户</h3>
              <p class="empty-description">
                请在右上角的租户选择器中选择一个租户，<br>
                然后就可以管理该租户下的部门了
              </p>
            </div>
          </div>
        </div>

        <OrgUnitsOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
        
        <!-- 删除确认对话框 -->
        <DeleteConfirmDialog
          v-model:visible="deleteConfirmVisible"
          :pre-check-data="deletePreCheckData"
          :loading="deletePreCheckLoading"
          @confirm="handleDeleteConfirm"
          @cancel="handleDeleteCancel"
        />
      </NCard>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.org-management-beautiful {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;

  // 页面头部美化
  .page-header-beautiful {
    margin-bottom: 20px;

    .header-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
      overflow: hidden;

      :deep(.n-card__content) {
        padding: 24px 32px;
      }
    }

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: white;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .header-icon {
      width: 48px;
      height: 48px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(10px);

      .icon {
        width: 28px;
        height: 28px;
        color: white;
      }
    }

    .header-text {
      .header-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0 0 4px 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .header-subtitle {
        font-size: 14px;
        opacity: 0.9;
        margin: 0;
        font-weight: 400;
      }
    }

    .header-right {
      .stats-mini {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);

        .stat-item {
          text-align: center;

          .stat-number {
            display: block;
            font-size: 24px;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 12px;
            opacity: 0.9;
            font-weight: 500;
          }
        }
      }
    }
  }

  // 搜索区域美化
  .search-section {
    margin-bottom: 20px;

    :deep(.n-card) {
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.5);
      backdrop-filter: blur(10px);
      background: rgba(255, 255, 255, 0.9);
    }
  }

  // 表格区域美化
  .table-section {
    .table-card {
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.5);
      backdrop-filter: blur(10px);
      background: rgba(255, 255, 255, 0.95);

      :deep(.n-card__content) {
        padding: 0;
      }
    }

    .table-header {
      padding: 20px 24px;
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
      background: linear-gradient(90deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
    }

    .table-container {
      padding: 0 24px 24px;

      .beautiful-table {
        background: transparent;

        :deep(.n-data-table-thead) {
          background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);

          .n-data-table-th {
            background: transparent;
            color: #475569;
            font-weight: 600;
            font-size: 13px;
            padding: 16px 12px;
            border-bottom: 2px solid #e2e8f0;

            &:first-child {
              border-top-left-radius: 8px;
            }

            &:last-child {
              border-top-right-radius: 8px;
            }
          }
        }

        :deep(.n-data-table-tbody) {
          .n-data-table-tr {
            transition: all 0.2s ease;

            &:hover {
              background: linear-gradient(90deg, rgba(102, 126, 234, 0.04) 0%, rgba(118, 75, 162, 0.04) 100%);
              transform: translateY(-1px);
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .n-data-table-td {
              padding: 16px 12px;
              border-bottom: 1px solid #f1f5f9;
              font-size: 14px;

              // 美化按钮组
              .flex-center {
                gap: 8px;

                .n-button {
                  border-radius: 6px;
                  font-weight: 500;
                  transition: all 0.2s ease;

                  &:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                  }
                }
              }
            }
          }

          // 隔行变色优化
          .n-data-table-tr--striped {
            background: rgba(248, 250, 252, 0.5);
          }
        }
      }
    }
  }

  // 空状态样式
  .empty-state,
  .no-tenant-state {
    padding: 60px 20px;
    text-align: center;
    
    .empty-content {
      max-width: 400px;
      margin: 0 auto;
      
      .empty-icon {
        margin-bottom: 24px;
        display: flex;
        justify-content: center;
        
        .icon {
          width: 80px;
          height: 80px;
          opacity: 0.6;
        }
      }
      
      .empty-title {
        font-size: 18px;
        font-weight: 600;
        color: #475569;
        margin: 0 0 12px 0;
      }
      
      .empty-description {
        font-size: 14px;
        color: #64748b;
        line-height: 1.6;
        margin: 0 0 32px 0;
      }
      
      .add-department-btn {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s ease;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .i-material-symbols\:add {
          font-size: 18px;
        }
      }
    }
  }
  
  .no-tenant-state {
    .empty-content {
      .empty-icon .icon {
        fill: none;
      }
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .org-management-beautiful {
    padding: 12px;

    .page-header-beautiful {
      .header-content {
        flex-direction: column;
        gap: 16px;
        text-align: center;

        .header-left {
          flex-direction: column;
          gap: 12px;
        }

        .header-right {
          .stats-mini {
            padding: 12px 16px;

            .stat-item {
              .stat-number {
                font-size: 20px;
              }

              .stat-label {
                font-size: 11px;
              }
            }
          }
        }
      }

      .header-text {
        .header-title {
          font-size: 20px;
        }

        .header-subtitle {
          font-size: 13px;
        }
      }
    }

    .table-section {
      .table-header {
        padding: 16px 20px;
      }

      .table-container {
        padding: 0 16px 20px;
      }
    }
  }
}

// 添加动画效果
.org-management-beautiful {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 卡片入场动画
.page-header-beautiful,
.search-section,
.table-section {
  animation: slideInFromLeft 0.8s ease-out;
}

.page-header-beautiful {
  animation-delay: 0.1s;
}

.search-section {
  animation-delay: 0.2s;
}

.table-section {
  animation-delay: 0.3s;
}

@keyframes slideInFromLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
