<script setup lang="tsx">
import {
  NBadge,
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NGi,
  NGrid,
  NInput,
  NProgress,
  NSelect,
  NSpace,
  NStatistic,
  NTag,
  NTooltip
} from 'naive-ui';
import { computed, h, onMounted, reactive, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { convertToBeijingTime } from '@/utils/date';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { $t } from '@/locales';
import {
  fetchGetAlertProcessingStats,
  fetchGetAlertProcessingSummary,
  fetchGetAutoProcessingLogs,
  fetchGetProcessingTrends
} from '@/service/api/health/alert-monitor';
import { useTable } from '@/hooks/common/table';

defineOptions({
  name: 'AlertMonitorPage'
});

const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 统计数据
const statsData = ref<Api.Health.AlertProcessingStats | null>(null);
const trendsData = ref<Api.Health.AlertProcessingTrend[]>([]);
const summaryData = ref<Api.Health.AlertProcessingSummary | null>(null);
const loading = ref(false);

// 搜索参数
const searchParams = reactive({
  startTime: '',
  endTime: '',
  severityLevel: '',
  processStatus: '',
  autoProcessed: null as boolean | null
});

// 时间范围快捷选择
const timeRangeOptions = [
  { label: '最近1小时', value: 'hour' },
  { label: '最近6小时', value: '6hour' },
  { label: '最近24小时', value: 'day' },
  { label: '最近7天', value: 'week' },
  { label: '最近30天', value: 'month' }
];

// 处理状态选项
const processStatusOptions = [
  { label: '待处理', value: 'PENDING' },
  { label: '处理中', value: 'PROCESSING' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '已忽略', value: 'IGNORED' },
  { label: '自动处理', value: 'AUTO_PROCESSED' }
];

// 严重程度选项
const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'Major', value: 'major' },
  { label: 'Minor', value: 'minor' },
  { label: 'Info', value: 'info' }
];

// 自动处理日志表格
const {
  data: logsData,
  loading: logsLoading,
  getData: getLogsData,
  searchParams: logsSearchParams,
  updateSearchParams: updateLogsSearchParams
} = useTable({
  apiFn: fetchGetAutoProcessingLogs,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    ...searchParams
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

// 日志表格列定义
const logsColumns = computed(() => [
  {
    key: 'index',
    title: '序号',
    width: 60,
    align: 'center'
  },
  {
    key: 'alertId',
    title: '告警ID',
    width: 100,
    align: 'center'
  },
  {
    key: 'deviceSn',
    title: '设备序列号',
    width: 150,
    align: 'center'
  },
  {
    key: 'alertType',
    title: '告警类型',
    width: 120,
    align: 'center'
  },
  {
    key: 'severityLevel',
    title: '严重程度',
    width: 100,
    align: 'center',
    render: (row: any) => h(NTag, { type: getSeverityColor(row.severityLevel) as any }, () => row.severityLevel)
  },
  {
    key: 'autoProcessAction',
    title: '处理动作',
    width: 120,
    align: 'center',
    render: (row: any) => h(NTag, { type: getActionColor(row.autoProcessAction) as any }, () => getActionText(row.autoProcessAction))
  },
  {
    key: 'processStatus',
    title: '处理状态',
    width: 100,
    align: 'center',
    render: (row: any) =>
      h(
        NBadge,
        {
          dot: true,
          type: getStatusColor(row.processStatus) as any
        },
        () => getStatusText(row.processStatus)
      )
  },
  {
    key: 'processTime',
    title: '处理时间',
    width: 150,
    align: 'center',
    render: (row: any) => convertToBeijingTime(row.processTime)
  },
  {
    key: 'processDuration',
    title: '处理耗时',
    width: 100,
    align: 'center',
    render: (row: any) => `${row.processDuration}ms`
  },
  {
    key: 'processResult',
    title: '处理结果',
    width: 150,
    align: 'center',
    render: (row: any) => row.processResult || '-'
  },
  {
    key: 'operate',
    title: '操作',
    width: 100,
    align: 'center',
    render: (row: any) => (
      <NButton type="primary" quaternary size="small" onClick={() => viewDetails(row)}>
        详情
      </NButton>
    )
  }
]);

// 获取严重程度颜色
function getSeverityColor(severity: string) {
  const colors = {
    critical: 'error',
    major: 'warning',
    minor: 'info',
    info: 'default'
  };
  return colors[severity as keyof typeof colors] || 'default';
}

// 获取处理动作颜色
function getActionColor(action: string) {
  const colors = {
    AUTO_RESOLVE: 'success',
    AUTO_ACKNOWLEDGE: 'info',
    AUTO_ESCALATE: 'warning',
    AUTO_SUPPRESS: 'error'
  };
  return colors[action as keyof typeof colors] || 'default';
}

// 获取处理动作文本
function getActionText(action: string) {
  const texts = {
    AUTO_RESOLVE: '自动解决',
    AUTO_ACKNOWLEDGE: '自动确认',
    AUTO_ESCALATE: '自动升级',
    AUTO_SUPPRESS: '自动抑制'
  };
  return texts[action as keyof typeof texts] || action;
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colors = {
    PENDING: 'default',
    PROCESSING: 'info',
    COMPLETED: 'success',
    FAILED: 'error',
    IGNORED: 'warning'
  };
  return colors[status as keyof typeof colors] || 'default';
}

// 获取状态文本
function getStatusText(status: string) {
  const texts = {
    PENDING: '待处理',
    PROCESSING: '处理中',
    COMPLETED: '已完成',
    FAILED: '失败',
    IGNORED: '已忽略'
  };
  return texts[status as keyof typeof texts] || status;
}

// 快捷时间选择
function handleTimeRangeSelect(value: string) {
  const now = new Date();
  let startTime = new Date();

  switch (value) {
    case 'hour':
      startTime = new Date(now.getTime() - 60 * 60 * 1000);
      break;
    case '6hour':
      startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
      break;
    case 'day':
      startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      break;
    case 'week':
      startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case 'month':
      startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
  }

  searchParams.startTime = startTime.toISOString().slice(0, 19);
  searchParams.endTime = now.toISOString().slice(0, 19);

  // 刷新数据
  loadAllData();
}

// 搜索
function handleSearch() {
  updateLogsSearchParams({
    ...logsSearchParams,
    ...searchParams,
    page: 1
  });
  getLogsData();
}

// 重置搜索
function handleReset() {
  Object.assign(searchParams, {
    startTime: '',
    endTime: '',
    severityLevel: '',
    processStatus: '',
    autoProcessed: null
  });
  handleSearch();
}

// 查看详情
function viewDetails(row: any) {
  // TODO: 实现详情查看功能
  console.log('查看详情:', row);
}

// 加载统计数据
async function loadStats() {
  const { data } = await fetchGetAlertProcessingStats({
    customerId,
    startTime: searchParams.startTime,
    endTime: searchParams.endTime
  });
  if (data) {
    statsData.value = data;
  }
}

// 加载趋势数据
async function loadTrends() {
  const { data } = await fetchGetProcessingTrends({
    customerId,
    startTime: searchParams.startTime,
    endTime: searchParams.endTime,
    granularity: 'hour' // 小时粒度
  });
  if (data) {
    trendsData.value = data;
  }
}

// 加载汇总数据
async function loadSummary() {
  const { data } = await fetchGetAlertProcessingSummary({
    customerId,
    period: 'today'
  });
  if (data) {
    summaryData.value = data;
  }
}

// 加载所有数据
async function loadAllData() {
  loading.value = true;
  try {
    await Promise.all([loadStats(), loadTrends(), loadSummary(), getLogsData()]);
  } finally {
    loading.value = false;
  }
}

// 自动刷新
function autoRefresh() {
  loadAllData();
}

// 初始化
onMounted(() => {
  // 默认加载最近24小时数据
  handleTimeRangeSelect('day');

  // 设置自动刷新（每30秒）
  setInterval(autoRefresh, 30000);
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 快捷时间选择 -->
    <NCard :bordered="false" class="card-wrapper">
      <div class="mb-4 flex items-center gap-4">
        <span class="text-sm font-medium">时间范围:</span>
        <NSpace>
          <NButton v-for="option in timeRangeOptions" :key="option.value" size="small" @click="handleTimeRangeSelect(option.value)">
            {{ option.label }}
          </NButton>
        </NSpace>
        <div class="flex-1"></div>
        <NButton :loading="loading" @click="loadAllData">刷新数据</NButton>
      </div>

      <!-- 自定义时间和筛选条件 -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-6">
        <NDatePicker v-model:formatted-value="searchParams.startTime" type="datetime" placeholder="开始时间" format="yyyy-MM-dd HH:mm:ss" />
        <NDatePicker v-model:formatted-value="searchParams.endTime" type="datetime" placeholder="结束时间" format="yyyy-MM-dd HH:mm:ss" />
        <NSelect v-model:value="searchParams.severityLevel" :options="severityOptions" placeholder="严重程度" clearable />
        <NSelect v-model:value="searchParams.processStatus" :options="processStatusOptions" placeholder="处理状态" clearable />
        <NSelect
          v-model:value="searchParams.autoProcessed"
          :options="[
            { label: '自动处理', value: true },
            { label: '人工处理', value: false }
          ]"
          placeholder="处理方式"
          clearable
        />
        <NSpace>
          <NButton type="primary" @click="handleSearch">查询</NButton>
          <NButton @click="handleReset">重置</NButton>
        </NSpace>
      </div>
    </NCard>

    <!-- 统计概览 -->
    <div v-if="statsData" class="grid grid-cols-1 gap-4 lg:grid-cols-4 md:grid-cols-2">
      <NCard size="small">
        <NStatistic label="总告警数" :value="statsData.totalAlerts">
          <template #suffix>
            <span class="text-xs text-gray-500">条</span>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small">
        <NStatistic label="自动处理数" :value="statsData.autoProcessedAlerts">
          <template #suffix>
            <span class="text-xs text-gray-500">条</span>
            <NTooltip>
              <template #trigger>
                <NTag size="small" type="success" class="ml-2">
                  {{ ((statsData.autoProcessedAlerts / statsData.totalAlerts) * 100).toFixed(1) }}%
                </NTag>
              </template>
              自动处理率
            </NTooltip>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small">
        <NStatistic label="平均处理时间" :value="statsData.avgProcessingTime">
          <template #suffix>
            <span class="text-xs text-gray-500">秒</span>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small">
        <NStatistic label="处理成功率" :value="statsData.successRate.toFixed(1)">
          <template #suffix>
            <span class="text-xs text-gray-500">%</span>
            <NProgress :percentage="statsData.successRate" type="line" :height="4" :show-indicator="false" class="mt-2" />
          </template>
        </NStatistic>
      </NCard>
    </div>

    <!-- 今日汇总 -->
    <div v-if="summaryData" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <NCard title="今日处理汇总" size="small">
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <div class="text-2xl text-blue-500 font-bold">{{ summaryData.todayTotal }}</div>
            <div class="text-sm text-gray-500">今日告警总数</div>
          </div>
          <div class="text-center">
            <div class="text-2xl text-green-500 font-bold">{{ summaryData.todayAutoProcessed }}</div>
            <div class="text-sm text-gray-500">自动处理数量</div>
          </div>
          <div class="text-center">
            <div class="text-2xl text-orange-500 font-bold">{{ summaryData.todayManualProcessed }}</div>
            <div class="text-sm text-gray-500">人工处理数量</div>
          </div>
          <div class="text-center">
            <div class="text-2xl text-red-500 font-bold">{{ summaryData.todayPending }}</div>
            <div class="text-sm text-gray-500">待处理数量</div>
          </div>
        </div>
      </NCard>

      <NCard title="处理效率对比" size="small">
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span>自动处理平均时间</span>
            <span class="text-green-500 font-bold">{{ summaryData.autoAvgTime }}s</span>
          </div>
          <div class="flex items-center justify-between">
            <span>人工处理平均时间</span>
            <span class="text-orange-500 font-bold">{{ summaryData.manualAvgTime }}s</span>
          </div>
          <div class="flex items-center justify-between">
            <span>效率提升</span>
            <span class="text-blue-500 font-bold">
              {{ (((summaryData.manualAvgTime - summaryData.autoAvgTime) / summaryData.manualAvgTime) * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 自动处理日志 -->
    <NCard title="自动处理日志" :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <NDataTable
        :data="logsData"
        :columns="logsColumns"
        :row-key="(row: any) => row.id"
        size="small"
        striped
        :loading="logsLoading"
        :scroll-x="1400"
      />
    </NCard>
  </div>
</template>

<style scoped>
.card-wrapper {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
</style>
