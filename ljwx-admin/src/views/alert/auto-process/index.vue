<script setup lang="tsx">
import { NBadge, NButton, NCard, NDataTable, NPopconfirm, NSpace, NSwitch, NTag, NTooltip } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, h, onMounted, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { convertToBeijingTime } from '@/utils/date';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import {
  fetchDeleteAlertAutoProcess,
  fetchGetAlertAutoProcessList,
  fetchGetAlertAutoProcessStats,
  fetchToggleAutoProcess
} from '@/service/api/health/alert-auto-process';
import TableHeaderOperation from '@/components/advanced/table-header-operation.vue';
import AlertAutoProcessSearch from './modules/alert-auto-process-search.vue';
import AlertAutoProcessOperateDrawer from './modules/alert-auto-process-operate-drawer.vue';

defineOptions({
  name: 'AlertAutoProcessPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');
const editingData: Ref<Api.Health.AlertAutoProcess | null> = ref(null);
const statsData = ref<Api.Health.AlertAutoProcessStats | null>(null);

const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 获取严重程度标签颜色
function getSeverityColor(severity: string) {
  const colors = {
    critical: 'error',
    major: 'warning',
    minor: 'info',
    info: 'default'
  };
  return colors[severity as keyof typeof colors] || 'default';
}

// 获取自动处理动作标签颜色
function getActionColor(action: string) {
  const colors = {
    AUTO_RESOLVE: 'success',
    AUTO_ACKNOWLEDGE: 'info',
    AUTO_ESCALATE: 'warning',
    AUTO_SUPPRESS: 'error'
  };
  return colors[action as keyof typeof colors] || 'default';
}

// 获取自动处理动作文本
function getActionText(action: string) {
  const texts = {
    AUTO_RESOLVE: '自动解决',
    AUTO_ACKNOWLEDGE: '自动确认',
    AUTO_ESCALATE: '自动升级',
    AUTO_SUPPRESS: '自动抑制'
  };
  return texts[action as keyof typeof texts] || action;
}

// 列定义
const tableColumns = computed(() => [
  {
    key: 'index',
    title: $t('common.index'),
    width: 64,
    align: 'center'
  },
  {
    key: 'physicalSign',
    title: '生理指标',
    align: 'center',
    width: 120,
    render: (row: Api.Health.AlertAutoProcess) => row.physicalSign || '-'
  },
  {
    key: 'alertType',
    title: '告警类型',
    align: 'center',
    width: 120,
    render: (row: Api.Health.AlertAutoProcess) => row.eventType || '-'
  },
  {
    key: 'severityLevel',
    title: '严重程度',
    align: 'center',
    width: 100,
    render: (row: Api.Health.AlertAutoProcess) => h(NTag, { type: getSeverityColor(row.level) as any }, () => row.level || '-')
  },
  {
    key: 'thresholds',
    title: '阈值范围',
    align: 'center',
    width: 150,
    render: (row: Api.Health.AlertAutoProcess) => {
      if (row.thresholdMin !== null && row.thresholdMax !== null) {
        return `${row.thresholdMin} - ${row.thresholdMax}`;
      } else if (row.thresholdMin !== null) {
        return `≥ ${row.thresholdMin}`;
      } else if (row.thresholdMax !== null) {
        return `≤ ${row.thresholdMax}`;
      }
      return '-';
    }
  },
  {
    key: 'autoProcessEnabled',
    title: '自动处理',
    align: 'center',
    width: 100,
    render: (row: Api.Health.AlertAutoProcess) =>
      h(NBadge, { dot: true, type: row.autoProcessEnabled ? 'success' : 'default' }, () => (row.autoProcessEnabled ? '已启用' : '已禁用'))
  },
  {
    key: 'autoProcessAction',
    title: '处理动作',
    align: 'center',
    width: 120,
    render: (row: Api.Health.AlertAutoProcess) =>
      row.autoProcessAction ? h(NTag, { type: getActionColor(row.autoProcessAction) as any }, () => getActionText(row.autoProcessAction)) : '-'
  },
  {
    key: 'autoProcessDelaySeconds',
    title: '延迟时间',
    align: 'center',
    width: 100,
    render: (row: Api.Health.AlertAutoProcess) => (row.autoProcessDelaySeconds ? `${row.autoProcessDelaySeconds}秒` : '-')
  },
  {
    key: 'suppressDurationMinutes',
    title: '抑制时长',
    align: 'center',
    width: 100,
    render: (row: Api.Health.AlertAutoProcess) => (row.suppressDurationMinutes ? `${row.suppressDurationMinutes}分钟` : '-')
  },
  {
    key: 'isEnabled',
    title: '规则状态',
    align: 'center',
    width: 100,
    render: (row: Api.Health.AlertAutoProcess) =>
      h(NSwitch, {
        value: row.isEnabled,
        'onUpdate:value': (value: boolean) => handleToggleRule(row.id, value),
        disabled: !hasAuth('alert:rules:edit')
      })
  },
  {
    key: 'updateTime',
    title: '更新时间',
    align: 'center',
    width: 150,
    render: (row: Api.Health.AlertAutoProcess) => convertToBeijingTime(row.updateTime)
  },
  {
    key: 'operate',
    title: $t('common.operate'),
    align: 'center',
    width: 160,
    render: (row: Api.Health.AlertAutoProcess) => (
      <NSpace size="small">
        {hasAuth('alert:rules:query') && (
          <NTooltip trigger="hover">
            {{
              default: () => '查看详情',
              trigger: () => (
                <NButton type="info" quaternary size="small" onClick={() => view(row)}>
                  详情
                </NButton>
              )
            }}
          </NTooltip>
        )}
        {hasAuth('alert:rules:edit') && (
          <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
            {$t('common.edit')}
          </NButton>
        )}
        {hasAuth('alert:rules:remove') && (
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
      </NSpace>
    )
  }
]);

const { data, loading, getData, getDataByPage, searchParams, updateSearchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertAutoProcessList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId
  },
  transformer: res => {
    const { records = [], page = 1, pageSize = 20, total = 0 } = res.data || {};
    const recordsWithIndex = records.map((item, index) => ({
      ...item,
      index: (page - 1) * pageSize + index + 1
    }));
    return { data: recordsWithIndex, pageNum: page, pageSize, total };
  }
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

// 操作函数
function handleAdd() {
  operateType.value = 'add';
  editingData.value = null;
  openDrawer();
}

function edit(item: Api.Health.AlertAutoProcess) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

function view(item: Api.Health.AlertAutoProcess) {
  operateType.value = 'view';
  editingData.value = { ...item };
  openDrawer();
}

// 删除单个规则
async function handleDelete(id: string) {
  const { error } = await fetchDeleteAlertAutoProcess(transDeleteParams([id]));
  if (!error) {
    await onDeleted();
    await loadStats(); // 刷新统计数据
  }
}

// 批量删除规则
async function handleBatchDelete() {
  const { error } = await fetchDeleteAlertAutoProcess(transDeleteParams(checkedRowKeys.value));
  if (!error) {
    await onBatchDeleted();
    await loadStats();
  }
}

// 切换规则启用状态
async function handleToggleRule(id: string, enabled: boolean) {
  const { error } = await fetchToggleAutoProcess({
    ids: [id],
    enabled
  });
  if (!error) {
    await getData();
    await loadStats();
  }
}

// 批量切换自动处理
async function handleBatchToggleAutoProcess(enabled: boolean) {
  if (checkedRowKeys.value.length === 0) {
    return;
  }

  const { error } = await fetchToggleAutoProcess({
    ids: checkedRowKeys.value,
    enabled
  });
  if (!error) {
    await getData();
    await loadStats();
    checkedRowKeys.value = []; // 清空选择
  }
}

// 加载统计数据
async function loadStats() {
  const { data: stats } = await fetchGetAlertAutoProcessStats({ customerId });
  if (stats) {
    statsData.value = stats;
  }
}

// 初始化
onMounted(async () => {
  await getData();
  await loadStats();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 统计卡片 -->
    <div v-if="statsData" class="grid grid-cols-1 mb-4 gap-4 md:grid-cols-4">
      <NCard size="small">
        <div class="text-center">
          <div class="text-2xl text-blue-500 font-bold">{{ statsData.totalRules }}</div>
          <div class="text-sm text-gray-500">总规则数</div>
        </div>
      </NCard>
      <NCard size="small">
        <div class="text-center">
          <div class="text-2xl text-green-500 font-bold">{{ statsData.autoProcessEnabledRules }}</div>
          <div class="text-sm text-gray-500">自动处理规则</div>
        </div>
      </NCard>
      <NCard size="small">
        <div class="text-center">
          <div class="text-2xl text-purple-500 font-bold">{{ statsData.autoProcessCoverageRate?.toFixed(1) }}%</div>
          <div class="text-sm text-gray-500">覆盖率</div>
        </div>
      </NCard>
      <NCard size="small">
        <div class="text-center">
          <div class="text-2xl text-orange-500 font-bold">{{ statsData.recentAutoProcessCount || 0 }}</div>
          <div class="text-sm text-gray-500">24h处理次数</div>
        </div>
      </NCard>
    </div>

    <!-- 搜索区域 -->
    <NCard :bordered="false" class="card-wrapper">
      <AlertAutoProcessSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    </NCard>

    <!-- 表格区域 -->
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <!-- 工具栏 -->
      <div class="mb-4 flex items-center justify-between">
        <NSpace>
          <NButton v-if="hasAuth('alert:rules:add')" type="primary" @click="handleAdd">新增规则</NButton>
          <NButton
            v-if="hasAuth('alert:rules:edit')"
            type="success"
            :disabled="checkedRowKeys.length === 0"
            @click="handleBatchToggleAutoProcess(true)"
          >
            批量启用自动处理
          </NButton>
          <NButton
            v-if="hasAuth('alert:rules:edit')"
            type="warning"
            :disabled="checkedRowKeys.length === 0"
            @click="handleBatchToggleAutoProcess(false)"
          >
            批量禁用自动处理
          </NButton>
          <NButton v-if="hasAuth('alert:rules:remove')" type="error" :disabled="checkedRowKeys.length === 0" @click="handleBatchDelete">
            批量删除
          </NButton>
        </NSpace>

        <NSpace>
          <NButton @click="loadStats">刷新统计</NButton>
          <NButton :loading="loading" @click="getData">刷新数据</NButton>
        </NSpace>
      </div>

      <!-- 表格 -->
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :data="data"
        :columns="tableColumns"
        :row-key="(row: any) => row.id"
        size="small"
        striped
        :loading="loading"
        :scroll-x="1400"
      />
    </NCard>

    <!-- 操作抽屉 -->
    <AlertAutoProcessOperateDrawer
      v-model:visible="drawerVisible"
      :operate-type="operateType"
      :row-data="editingData"
      @submitted="
        async () => {
          await getDataByPage();
          await loadStats();
        }
      "
    />
  </div>
</template>

<style scoped>
.card-wrapper {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
</style>
