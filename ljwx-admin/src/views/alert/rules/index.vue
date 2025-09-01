<script setup lang="tsx">
import { NButton, NPopconfirm, NCollapse, NCollapseItem, NAlert, NList, NListItem, NIcon, NSpace } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAlertRules, fetchGetAlertRulesList } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import AlerrulesSearch from './modules/alerrules-search.vue';
import AlerrulesOperateDrawer from './modules/alerrules-operate-drawer.vue';
defineOptions({
  name: 'TAlertRulesPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.AlertRules | null> = ref(null);
const customerId = authStore.userInfo?.customerId;
const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertRulesList,
  apiParams: {
    page: 1,
    pageSize: 20,
    ruleType: null,
    customerId,
    physicalSign: null
  },
  columns: () => [
    { type: 'selection', width: 40, align: 'center' },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'ruleType',
      title: $t('page.health.alert.rules.ruleType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_type', row.ruleType)
    },
    {
      key: 'physicalSign',
      title: $t('page.health.alert.rules.physicalSign'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('health_data_type', row.physicalSign)
    },
    {
      key: 'thresholdMin',
      title: $t('page.health.alert.rules.thresholdMin'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'thresholdMax',
      title: $t('page.health.alert.rules.thresholdMax'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'trendDuration',
      title: $t('page.health.alert.rules.trendDuration'),
      align: 'center',
      minWidth: 100
    },

    {
      key: 'alertMessage',
      title: $t('page.health.alert.rules.alertMessage'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'notificationType',
      title: $t('page.health.alert.rules.notificationType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('notification_type', row.notificationType)
    },
    {
      key: 'severityLevel',
      title: $t('page.health.alert.rules.severityLevel'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_severityLevel', row.severityLevel)
    },
    {
      key: 'createUser',
      title: $t('page.health.alert.rules.createUser'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'createTime',
      title: $t('page.health.alert.rules.createTime'),
      align: 'center',
      minWidth: 100,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:alert:rules:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:alert:rules:delete') && (
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

function edit(item: Api.Health.AlertRules) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

// 操作手册展开状态
const manualExpanded = ref(false);
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 操作手册 -->
    <NCard :bordered="false" size="small" class="operation-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="📋 告警规则操作手册">
          <template #header-extra>
            <NSpace>
              <span class="text-xs text-gray-500">点击展开查看详细操作说明</span>
            </NSpace>
          </template>
          
          <div class="manual-content">
            <NAlert type="info" :show-icon="false" class="mb-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="16">
                    <i class="i-material-symbols:info"></i>
                  </NIcon>
                  <span class="font-semibold">系统概述</span>
                </div>
              </template>
              告警规则用于监控用户健康数据，当数据超出设定阈值时自动触发告警通知
            </NAlert>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- 基础操作 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="16" color="#3b82f6">
                      <i class="i-material-symbols:settings"></i>
                    </NIcon>
                    <span class="font-medium">基础操作</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">1</span>
                      <div>
                        <div class="item-title">新增规则</div>
                        <div class="item-desc">点击"新增"按钮创建新的告警规则</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">2</span>
                      <div>
                        <div class="item-title">编辑规则</div>
                        <div class="item-desc">点击"编辑"按钮修改现有规则参数</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">3</span>
                      <div>
                        <div class="item-title">删除规则</div>
                        <div class="item-desc">选择规则后点击"删除"按钮移除规则</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>

              <!-- 规则配置 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="16" color="#10b981">
                      <i class="i-material-symbols:rule"></i>
                    </NIcon>
                    <span class="font-medium">规则配置</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">阈值</span>
                      <div>
                        <div class="item-title">设置数值范围</div>
                        <div class="item-desc">配置最小值和最大值触发条件</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">级别</span>
                      <div>
                        <div class="item-title">选择严重程度</div>
                        <div class="item-desc">低、中、高、紧急四个级别</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">通知</span>
                      <div>
                        <div class="item-title">配置通知方式</div>
                        <div class="item-desc">微信、短信、邮件等通知渠道</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>
            </div>

            <!-- 常见示例 -->
            <NCard size="small" class="manual-section mt-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="16" color="#f59e0b">
                    <i class="i-material-symbols:lightbulb"></i>
                  </NIcon>
                  <span class="font-medium">配置示例</span>
                </div>
              </template>
              <div class="examples-grid">
                <div class="example-item">
                  <div class="example-title">心率异常监控</div>
                  <div class="example-content">
                    <span class="example-param">类型: 心率</span>
                    <span class="example-param">范围: 60-100 bpm</span>
                    <span class="example-param">级别: 高</span>
                  </div>
                </div>
                <div class="example-item">
                  <div class="example-title">血氧低值预警</div>
                  <div class="example-content">
                    <span class="example-param">类型: 血氧</span>
                    <span class="example-param">最小值: 95%</span>
                    <span class="example-param">级别: 紧急</span>
                  </div>
                </div>
                <div class="example-item">
                  <div class="example-title">血压高值告警</div>
                  <div class="example-content">
                    <span class="example-param">类型: 血压</span>
                    <span class="example-param">最大值: 140/90</span>
                    <span class="example-param">级别: 中</span>
                  </div>
                </div>
              </div>
            </NCard>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <AlerrulesSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:alert:rules:add"
        delete-auth="t:alert:rules:delete"
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
      <AlerrulesOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>

<style scoped>
/* 操作手册样式 */
.operation-manual {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.manual-content {
  padding: 8px;
}

.manual-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.manual-section:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.manual-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 0;
}

.item-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.item-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
  min-width: 40px;
}

.item-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  margin-bottom: 2px;
}

.item-desc {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.example-item {
  padding: 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.example-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.example-title {
  font-weight: 600;
  color: #92400e;
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.example-title::before {
  content: "💡";
  font-size: 12px;
}

.example-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.example-param {
  font-size: 11px;
  color: #78350f;
  background: rgba(255, 255, 255, 0.6);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #fbbf24;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .examples-grid {
    grid-template-columns: 1fr;
  }
  
  .manual-content {
    padding: 4px;
  }
}

/* 折叠面板样式优化 */
:deep(.n-collapse .n-collapse-item .n-collapse-item__header) {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 6px;
  padding: 12px 16px;
  font-weight: 600;
  color: #1e293b;
}

:deep(.n-collapse .n-collapse-item .n-collapse-item__content-wrapper) {
  border-top: 1px solid #e2e8f0;
  margin-top: 8px;
}
</style>
