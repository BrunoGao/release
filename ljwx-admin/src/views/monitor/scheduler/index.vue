<script setup lang="tsx">
import { NAlert, NButton, NCard, NCollapse, NCollapseItem, NIcon, NList, NListItem, NPopconfirm, NTag } from 'naive-ui';
import { h, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { $t } from '@/locales';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { fetchDeleteScheduler, fetchGetSchedulerList } from '@/service/api';
import { transDeleteParams } from '@/utils/common';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import SvgIcon from '@/components/custom/svg-icon.vue';
import { useButtonAuthDropdown } from '@/hooks/common/button-auth-dropdown';
import { useDict } from '@/hooks/business/dict';
import { formatDateTime } from '@/utils/date';
import SchedulerSearch from './modules/scheduler-search.vue';
import SchedulerOperateDrawer from './modules/scheduler-operate-drawer.vue';
import type { ButtonDropdownKey } from './modules/shared';
import { getOperationConfig } from './modules/shared';

defineOptions({
  name: 'MonScheduler'
});

const appStore = useAppStore();

const { hasAuth } = useAuth();

const { dictTag } = useDict();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 使用手册展开状态
const manualExpanded = ref(['manual']);

/** operation options */
const options: CommonType.ButtonDropdown<ButtonDropdownKey, Api.Monitor.Scheduler>[] = [
  {
    key: 'immediate',
    label: $t('page.monitor.scheduler.immediateJob'),
    show: hasAuth('mon:scheduler:immediate'),
    icon: () => h(SvgIcon, { icon: 'ic:baseline-play-arrow' }),
    handler: (key, row) => handleOperation(key, row)
  },
  {
    key: 'pause',
    show: hasAuth('mon:scheduler:pause'),
    label: $t('page.monitor.scheduler.pauseJob'),
    icon: () => h(SvgIcon, { icon: 'ic:baseline-pause' }),
    handler: (key, row) => handleOperation(key, row)
  },
  {
    key: 'pauseGroup',
    show: hasAuth('mon:scheduler:pauseGroup'),
    label: $t('page.monitor.scheduler.pauseJobGroup'),
    icon: () => h(SvgIcon, { icon: 'ic:baseline-pause-circle' }),
    handler: (key, row) => handleOperation(key, row)
  },
  {
    key: 'resume',
    show: hasAuth('mon:scheduler:resume'),
    label: $t('page.monitor.scheduler.resumeJob'),
    icon: () => h(SvgIcon, { icon: 'ic:baseline-wifi-protected-setup' }),
    handler: (key, row) => handleOperation(key, row)
  },
  {
    key: 'resumeGroup',
    show: hasAuth('mon:scheduler:resumeGroup'),
    label: $t('page.monitor.scheduler.resumeJobGroup'),
    icon: () => h(SvgIcon, { icon: 'ic:round-auto-awesome-motion' }),
    handler: (key, row) => handleOperation(key, row)
  }
];

const { renderDropdown } = useButtonAuthDropdown(options);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetSchedulerList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    jobName: null,
    jobGroup: null
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48,
      fixed: 'left'
    },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'triggerState',
      title: $t('page.monitor.scheduler.triggerState'),
      align: 'center',
      width: 100,
      render: row => dictTag('scheduler_trigger_status', row.triggerState)
    },
    {
      key: 'jobName',
      title: $t('page.monitor.scheduler.jobName'),
      align: 'center',
      width: 140,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'jobGroup',
      title: $t('page.monitor.scheduler.jobGroup'),
      align: 'center',
      width: 140,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'jobClassName',
      title: $t('page.monitor.scheduler.jobClassName'),
      align: 'center',
      width: 300,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'cronExpression',
      title: $t('page.monitor.scheduler.cronExpression'),
      align: 'center',
      minWidth: 200,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'description',
      title: $t('page.monitor.scheduler.description'),
      align: 'center',
      width: 200,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'triggerName',
      title: $t('page.monitor.scheduler.triggerName'),
      align: 'center',
      width: 140,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'triggerGroup',
      title: $t('page.monitor.scheduler.triggerGroup'),
      align: 'center',
      width: 140,
      ellipsis: {
        tooltip: true
      },
      resizable: true
    },
    {
      key: 'triggerDescription',
      title: $t('page.monitor.scheduler.triggerDescription'),
      align: 'center',
      minWidth: 200,
      ellipsis: {
        tooltip: true
      }
    },
    {
      key: 'createUser',
      title: $t('common.createUser'),
      align: 'center',
      width: 120
    },
    {
      key: 'createTime',
      title: $t('common.createTime'),
      align: 'center',
      width: 200,
      render: row => formatDateTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      fixed: 'right',
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('mon:scheduler:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('mon:scheduler:delete') && (
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
          {renderDropdown(row)}
        </div>
      )
    }
  ]
});

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onDeleted, onBatchDeleted, onMessage } = useTableOperate(
  data,
  getData
);

function edit(id: string) {
  handleEdit(id);
}

// handle operation
function handleOperation(key: ButtonDropdownKey, row: Api.Monitor.Scheduler) {
  // get config
  const config = getOperationConfig(key, row);
  // show dialog
  window.$dialog?.warning({
    ...config,
    onPositiveClick: async () => {
      const res = await config.onPositiveClick();
      if (!res.error && res.data) {
        onMessage(config.message);
      }
    }
  });
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteScheduler(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteScheduler(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 使用手册 -->
    <NCard :bordered="false" class="user-manual-card" content-class="p-4">
      <NCollapse v-model:expanded-names="manualExpanded" display-directive="show">
        <NCollapseItem name="manual">
          <template #header>
            <div class="flex items-center gap-2">
              <NIcon size="20" color="#3b82f6">
                <i class="i-material-symbols:schedule"></i>
              </NIcon>
              <span class="text-lg text-gray-800 font-semibold">定时任务调度管理使用手册</span>
              <NTag type="info" size="small">点击展开/收起</NTag>
            </div>
          </template>

          <div class="grid grid-cols-1 mt-4 gap-4 lg:grid-cols-2">
            <!-- 健康任务说明 -->
            <div>
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="18" color="#10b981">
                      <i class="i-material-symbols:health-and-safety"></i>
                    </NIcon>
                    <span class="text-green-700 font-medium">健康定时任务说明</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">🔍</span>
                      <div>
                        <div class="item-title">权重配置验证 (01:00)</div>
                        <div class="item-desc">验证健康数据权重配置的正确性</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">📊</span>
                      <div>
                        <div class="item-title">基线和评分生成 (02:00-04:10)</div>
                        <div class="item-desc">生成用户、部门、组织健康基线和评分数据</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">🎯</span>
                      <div>
                        <div class="item-title">健康建议生成 (03:00)</div>
                        <div class="item-desc">基于健康数据分析生成个性化建议</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">🗑️</span>
                      <div>
                        <div class="item-title">数据清理 (05:00)</div>
                        <div class="item-desc">清理过期数据，保持系统性能</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>
            </div>

            <!-- 操作指南 -->
            <div>
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="18" color="#f59e0b">
                      <i class="i-material-symbols:touch-app"></i>
                    </NIcon>
                    <span class="text-amber-700 font-medium">操作功能指南</span>
                  </div>
                </template>

                <div class="grid grid-cols-1 mt-3 gap-4">
                  <div class="operation-guide">
                    <div class="guide-header">
                      <NIcon size="16" color="#3b82f6">
                        <i class="i-material-symbols:play-arrow"></i>
                      </NIcon>
                      <span class="guide-title">任务执行控制</span>
                    </div>
                    <div class="guide-content">
                      <div class="guide-step">
                        •
                        <strong>立即执行</strong>
                        ：点击操作按钮中的"立即执行"测试任务
                      </div>
                      <div class="guide-step">
                        •
                        <strong>暂停/恢复</strong>
                        ：控制任务的启用状态
                      </div>
                      <div class="guide-step">
                        •
                        <strong>批量操作</strong>
                        ：选择多个任务进行批量管理
                      </div>
                    </div>
                  </div>

                  <div class="operation-guide">
                    <div class="guide-header">
                      <NIcon size="16" color="#10b981">
                        <i class="i-material-symbols:edit"></i>
                      </NIcon>
                      <span class="guide-title">任务配置管理</span>
                    </div>
                    <div class="guide-content">
                      <div class="guide-step">
                        •
                        <strong>编辑任务</strong>
                        ：修改Cron表达式和任务描述
                      </div>
                      <div class="guide-step">
                        •
                        <strong>查看状态</strong>
                        ：监控任务运行状态和执行历史
                      </div>
                      <div class="guide-step">
                        •
                        <strong>添加任务</strong>
                        ：创建新的定时任务
                      </div>
                    </div>
                  </div>

                  <div class="operation-guide">
                    <div class="guide-header">
                      <NIcon size="16" color="#ef4444">
                        <i class="i-material-symbols:warning"></i>
                      </NIcon>
                      <span class="guide-title">注意事项</span>
                    </div>
                    <div class="guide-content">
                      <div class="guide-step">
                        •
                        <strong>健康任务</strong>
                        ：系统预置的健康相关任务请勿随意删除
                      </div>
                      <div class="guide-step">
                        •
                        <strong>时间设置</strong>
                        ：修改执行时间时注意避免任务冲突
                      </div>
                      <div class="guide-step">
                        •
                        <strong>监控日志</strong>
                        ：定期查看任务执行日志确保正常运行
                      </div>
                    </div>
                  </div>
                </div>
              </NCard>
            </div>
          </div>

          <!-- 状态说明 -->
          <NAlert type="info" class="mt-4">
            <template #icon>
              <NIcon size="18">
                <i class="i-material-symbols:info"></i>
              </NIcon>
            </template>
            <div>
              <div class="mb-2 font-medium">任务状态说明：</div>
              <div class="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
                <div>
                  <NTag type="success" size="small">WAITING</NTag>
                  等待执行
                </div>
                <div>
                  <NTag type="info" size="small">RUNNING</NTag>
                  正在执行
                </div>
                <div>
                  <NTag type="warning" size="small">PAUSED</NTag>
                  已暂停
                </div>
                <div>
                  <NTag type="error" size="small">ERROR</NTag>
                  执行错误
                </div>
              </div>
            </div>
          </NAlert>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <SchedulerSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="mon:scheduler:add"
        delete-auth="mon:scheduler:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #suffix></template>
      </TableHeaderOperation>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="1500"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :single-column="true"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
      <SchedulerOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
