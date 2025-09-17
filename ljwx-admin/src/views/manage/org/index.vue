<script setup lang="tsx">
import { NButton, NPopconfirm } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, ref } from 'vue';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { fetchDeleteOrgUnits, fetchGetOrgUnitsPageList } from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { transDeleteParams } from '@/utils/common';
import { useDict } from '@/hooks/business/dict';
import OrgUnitsOperateDrawer, { type OperateType } from './modules/org-units-operate-drawer.vue';
import OrgUnitsSearch from './modules/org-units-search.vue';

defineOptions({
  name: 'OrgUnitsPage'
});

const appStore = useAppStore();

const { hasAuth } = useAuth();

const authStore = useAuthStore();

const { dictTag } = useDict();

// 判断是否是超级管理员（admin用户，可以管理所有租户）
const isAdmin = computed(() => {
  return authStore.userInfo?.userName === 'admin';
});

// 判断是否是租户管理员（只能管理自己租户）
const isTenantAdmin = computed(() => {
  return authStore.userInfo?.roleIds?.includes('R_ADMIN') && !isAdmin.value;
});

const operateType = ref<OperateType>('add');

const editingData: Ref<Api.SystemManage.OrgUnits | null> = ref(null);

// 获取customerId
const customerId = computed(() => authStore.userInfo?.customerId || 0);

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
      title: isAdmin.value ? $t('page.manage.orgUnits.name') : $t('page.manage.orgUnits.dept.name'),
      align: 'center',
      width: 150,
      minWidth: 150,
      render: row => row.name || '-'
    },
    {
      key: 'code',
      title: isAdmin.value ? $t('page.manage.orgUnits.code') : $t('page.manage.orgUnits.dept.code'),
      align: 'center',
      width: 100,
      minWidth: 100,
      render: row => row.code || '-'
    },
    {
      key: 'abbr',
      title: isAdmin.value ? $t('page.manage.orgUnits.abbr') : $t('page.manage.orgUnits.dept.abbr'),
      align: 'center',
      width: 100,
      minWidth: 100,
      render: row => row.abbr || '-'
    },
    {
      key: 'description',
      title: isAdmin.value ? $t('page.manage.orgUnits.description') : $t('page.manage.orgUnits.dept.description'),
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
      title: isAdmin.value ? $t('page.manage.orgUnits.status') : $t('page.manage.orgUnits.dept.status'),
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
          {hasAuth('sys:org:units:add') && (
            <NButton type="primary" quaternary size="small" onClick={() => handleAddChildOrgUnits(row)}>
              {$t('page.manage.orgUnits.addChildOrgUnits')}
            </NButton>
          )}
          {hasAuth('sys:org:units:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('sys:org:units:delete') && (
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

function edit(item: Api.SystemManage.OrgUnits) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteOrgUnits(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

async function handleAddChildOrgUnits(item: Api.SystemManage.OrgUnits) {
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
                <path d="M12 2L2 7V10C2 16 6 20.5 12 22C18 20.5 22 16 22 10V7L12 2Z" stroke="currentColor" stroke-width="2" fill="url(#gradient)"/>
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="header-text">
              <h1 class="header-title">{{ isAdmin ? '租户与部门管理' : '部门管理' }}</h1>
              <p class="header-subtitle">
                {{ isAdmin ? '超级管理员可以创建租户和管理所有部门' : '租户管理员只能管理本租户下的部门' }}
              </p>
            </div>
          </div>
          <div class="header-right">
            <div class="stats-mini">
              <div class="stat-item">
                <span class="stat-number">{{ data?.length || 0 }}</span>
                <span class="stat-label">{{ isAdmin ? '组织数量' : '部门数量' }}</span>
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
            :add-auth="isAdmin ? 'sys:org:units:add' : false"
            delete-auth="sys:org:units:delete"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @refresh="getData"
          />
        </div>
        
        <div class="table-container">
          <NDataTable
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
        </div>

        <OrgUnitsOperateDrawer 
          v-model:visible="drawerVisible" 
          :operate-type="operateType" 
          :row-data="editingData" 
          @submitted="getDataByPage" 
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
