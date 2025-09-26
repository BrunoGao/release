<script setup lang="tsx">
import { NButton, NCard, NDataTable, NDatePicker, NSelect, NSpace, NTag, NBadge, useMessage } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, onMounted, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { $t } from '@/locales';
import { 
  fetchGetGeofenceAlertList, 
  fetchProcessGeofenceAlert, 
  fetchBatchProcessGeofenceAlerts,
  fetchGetGeofenceAlertStats,
  fetchGetRecentGeofenceAlerts
} from '@/service/api';
import type { Api } from '@/typings';

defineOptions({
  name: 'GeofenceAlertPage'
});

const message = useMessage();

// 查询参数
const searchParams = ref<Api.Geofence.GeofenceAlertSearchParams>({
  pageNum: 1,
  pageSize: 20,
  userId: undefined,
  fenceId: undefined,
  eventType: undefined,
  alertStatus: undefined,
  alertLevel: undefined,
  startTime: '',
  endTime: ''
});

// 数据状态
const alertData = ref<Api.Geofence.GeofenceAlert[]>([]);
const alertStats = ref<Api.Geofence.GeofenceAlertStats | null>(null);
const loading = ref(false);
const total = ref(0);
const checkedRowKeys = ref<string[]>([]);

// 选项配置
const eventTypeOptions = [
  { label: '全部', value: '' },
  { label: '进入围栏', value: 'ENTER' },
  { label: '离开围栏', value: 'EXIT' },
  { label: '停留超时', value: 'STAY_TIMEOUT' }
];

const alertStatusOptions = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'PENDING' },
  { label: '处理中', value: 'PROCESSING' },
  { label: '已处理', value: 'PROCESSED' },
  { label: '已忽略', value: 'IGNORED' }
];

const alertLevelOptions = [
  { label: '全部', value: '' },
  { label: '低级', value: 'LOW' },
  { label: '中级', value: 'MEDIUM' },
  { label: '高级', value: 'HIGH' }
];

// 状态标签颜色
const getStatusType = (status: string) => {
  switch (status) {
    case 'PENDING': return 'warning';
    case 'PROCESSING': return 'info'; 
    case 'PROCESSED': return 'success';
    case 'IGNORED': return 'default';
    default: return 'default';
  }
};

const getLevelType = (level: string) => {
  switch (level) {
    case 'LOW': return 'success';
    case 'MEDIUM': return 'warning';
    case 'HIGH': return 'error';
    default: return 'default';
  }
};

const getEventTypeText = (type: string) => {
  switch (type) {
    case 'ENTER': return '进入围栏';
    case 'EXIT': return '离开围栏';
    case 'STAY_TIMEOUT': return '停留超时';
    default: return type;
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'PENDING': return '待处理';
    case 'PROCESSING': return '处理中';
    case 'PROCESSED': return '已处理';
    case 'IGNORED': return '已忽略';
    default: return status;
  }
};

const getLevelText = (level: string) => {
  switch (level) {
    case 'LOW': return '低级';
    case 'MEDIUM': return '中级';
    case 'HIGH': return '高级';
    default: return level;
  }
};

// 表格列定义
const columns: DataTableColumns<Api.Geofence.GeofenceAlert> = [
  {
    type: 'selection',
    key: 'selection'
  },
  {
    key: 'alertId',
    title: '告警ID',
    width: 120,
    ellipsis: {
      tooltip: true
    },
    render: (row) => row.alertId.substring(0, 8) + '...'
  },
  {
    key: 'fenceName',
    title: '围栏名称',
    width: 120,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'userId',
    title: '用户ID',
    width: 80
  },
  {
    key: 'eventType',
    title: '事件类型',
    width: 100,
    render: (row) => (
      <NTag type={row.eventType === 'ENTER' ? 'success' : row.eventType === 'EXIT' ? 'warning' : 'error'}>
        {getEventTypeText(row.eventType)}
      </NTag>
    )
  },
  {
    key: 'alertLevel',
    title: '告警级别',
    width: 100,
    render: (row) => (
      <NTag type={getLevelType(row.alertLevel)}>
        {getLevelText(row.alertLevel)}
      </NTag>
    )
  },
  {
    key: 'alertStatus',
    title: '处理状态',
    width: 100,
    render: (row) => (
      <NTag type={getStatusType(row.alertStatus)}>
        {getStatusText(row.alertStatus)}
      </NTag>
    )
  },
  {
    key: 'eventTime',
    title: '事件时间',
    width: 150,
    render: (row) => new Date(row.eventTime).toLocaleString()
  },
  {
    key: 'location',
    title: '位置',
    width: 150,
    render: (row) => `${row.locationLng.toFixed(6)}, ${row.locationLat.toFixed(6)}`
  },
  {
    key: 'processTime',
    title: '处理时间',
    width: 150,
    render: (row) => row.processTime ? new Date(row.processTime).toLocaleString() : '-'
  },
  {
    key: 'actions',
    title: '操作',
    width: 200,
    render: (row) => (
      <NSpace>
        {row.alertStatus === 'PENDING' && (
          <>
            <NButton size="small" type="primary" onClick={() => handleProcessAlert(row.alertId, 'PROCESSING')}>
              处理
            </NButton>
            <NButton size="small" type="success" onClick={() => handleProcessAlert(row.alertId, 'PROCESSED')}>
              完成
            </NButton>
            <NButton size="small" type="warning" onClick={() => handleProcessAlert(row.alertId, 'IGNORED')}>
              忽略
            </NButton>
          </>
        )}
        {row.alertStatus === 'PROCESSING' && (
          <>
            <NButton size="small" type="success" onClick={() => handleProcessAlert(row.alertId, 'PROCESSED')}>
              完成
            </NButton>
            <NButton size="small" type="warning" onClick={() => handleProcessAlert(row.alertId, 'IGNORED')}>
              忽略
            </NButton>
          </>
        )}
        {(row.alertStatus === 'PROCESSED' || row.alertStatus === 'IGNORED') && (
          <NTag type="default">已处理</NTag>
        )}
      </NSpace>
    )
  }
];

// 查询告警数据
async function queryAlertData() {
  loading.value = true;
  try {
    const result = await fetchGetGeofenceAlertList(searchParams.value);
    if (result.data) {
      alertData.value = result.data.records || [];
      total.value = result.data.total || 0;
    }
    
    // 获取统计信息
    const statsResult = await fetchGetGeofenceAlertStats(searchParams.value);
    if (statsResult.data) {
      alertStats.value = statsResult.data;
    }
    
    message.success(`查询完成，获取到 ${alertData.value.length} 条告警记录`);
  } catch (error) {
    message.error('查询失败：' + error);
    console.error('Query alert data error:', error);
  } finally {
    loading.value = false;
  }
}

// 处理单个告警
async function handleProcessAlert(alertId: string, newStatus: 'PROCESSING' | 'PROCESSED' | 'IGNORED', processNote?: string) {
  try {
    const result = await fetchProcessGeofenceAlert({
      alertId,
      newStatus,
      processNote
    });
    
    if (result.data) {
      message.success('告警处理成功');
      queryAlertData(); // 刷新数据
    } else {
      message.error('告警处理失败');
    }
  } catch (error) {
    message.error('告警处理失败：' + error);
    console.error('Process alert error:', error);
  }
}

// 批量处理告警
async function handleBatchProcess(newStatus: 'PROCESSING' | 'PROCESSED' | 'IGNORED') {
  if (checkedRowKeys.value.length === 0) {
    message.warning('请选择要处理的告警记录');
    return;
  }
  
  try {
    const processData = checkedRowKeys.value.map(alertId => ({
      alertId,
      newStatus,
      processNote: `批量${getStatusText(newStatus)}`
    }));
    
    const result = await fetchBatchProcessGeofenceAlerts(processData);
    if (result.data) {
      const successCount = Object.values(result.data).filter(success => success).length;
      message.success(`批量处理完成，成功处理 ${successCount} 条告警`);
      checkedRowKeys.value = [];
      queryAlertData(); // 刷新数据
    } else {
      message.error('批量处理失败');
    }
  } catch (error) {
    message.error('批量处理失败：' + error);
    console.error('Batch process error:', error);
  }
}

// 时间范围处理
function handleTimeRangeChange(value: [number, number] | null) {
  if (value) {
    searchParams.value.startTime = new Date(value[0]).toISOString();
    searchParams.value.endTime = new Date(value[1]).toISOString();
  } else {
    searchParams.value.startTime = '';
    searchParams.value.endTime = '';
  }
}

// 获取默认时间范围（最近7天）
function getDefaultTimeRange(): [number, number] {
  const end = new Date();
  const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
  return [start.getTime(), end.getTime()];
}

// 分页处理
function handlePageChange(page: number) {
  searchParams.value.pageNum = page;
  queryAlertData();
}

function handlePageSizeChange(pageSize: number) {
  searchParams.value.pageSize = pageSize;
  searchParams.value.pageNum = 1;
  queryAlertData();
}

// 导出功能
function exportAlertData() {
  if (alertData.value.length === 0) {
    message.warning('没有告警数据可导出');
    return;
  }
  
  const csvContent = 'data:text/csv;charset=utf-8,' + 
    '告警ID,围栏名称,用户ID,事件类型,告警级别,处理状态,事件时间,位置经度,位置纬度,处理时间\n' +
    alertData.value.map(alert => [
      alert.alertId,
      alert.fenceName,
      alert.userId,
      getEventTypeText(alert.eventType),
      getLevelText(alert.alertLevel),
      getStatusText(alert.alertStatus),
      new Date(alert.eventTime).toLocaleString(),
      alert.locationLng,
      alert.locationLat,
      alert.processTime ? new Date(alert.processTime).toLocaleString() : ''
    ].join(',')).join('\n');
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `geofence_alerts_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  message.success('告警数据已导出');
}

onMounted(() => {
  // 设置默认时间范围
  const defaultRange = getDefaultTimeRange();
  handleTimeRangeChange(defaultRange);
  queryAlertData();
});
</script>

<template>
  <div class="geofence-alert-management">
    <!-- 统计卡片 -->
    <div v-if="alertStats" class="stats-cards mb-4">
      <NSpace>
        <NCard size="small">
          <div class="stat-item">
            <div class="stat-value">{{ alertStats.total }}</div>
            <div class="stat-label">总告警数</div>
          </div>
        </NCard>
        <NCard size="small">
          <NBadge :value="alertStats.pending" type="warning">
            <div class="stat-item">
              <div class="stat-value">{{ alertStats.pending }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </NBadge>
        </NCard>
        <NCard size="small">
          <NBadge :value="alertStats.processing" type="info">
            <div class="stat-item">
              <div class="stat-value">{{ alertStats.processing }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </NBadge>
        </NCard>
        <NCard size="small">
          <div class="stat-item">
            <div class="stat-value">{{ alertStats.processed }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </NCard>
        <NCard size="small">
          <NBadge :value="alertStats.levelStats.high" type="error">
            <div class="stat-item">
              <div class="stat-value">{{ alertStats.levelStats.high }}</div>
              <div class="stat-label">高级告警</div>
            </div>
          </NBadge>
        </NCard>
      </NSpace>
    </div>

    <!-- 查询条件 -->
    <NCard title="查询条件" class="mb-4">
      <NSpace vertical>
        <NSpace align="center">
          <span class="label">事件类型：</span>
          <NSelect
            v-model:value="searchParams.eventType"
            :options="eventTypeOptions"
            style="width: 150px"
          />
          
          <span class="label">告警状态：</span>
          <NSelect
            v-model:value="searchParams.alertStatus"
            :options="alertStatusOptions"
            style="width: 150px"
          />
          
          <span class="label">告警级别：</span>
          <NSelect
            v-model:value="searchParams.alertLevel"
            :options="alertLevelOptions"
            style="width: 150px"
          />
        </NSpace>
        
        <NSpace align="center">
          <span class="label">时间范围：</span>
          <NDatePicker
            :value="searchParams.startTime && searchParams.endTime ? [new Date(searchParams.startTime).getTime(), new Date(searchParams.endTime).getTime()] : null"
            type="datetimerange"
            @update:value="handleTimeRangeChange"
            style="width: 350px"
          />
        </NSpace>
        
        <NSpace>
          <NButton type="primary" @click="queryAlertData" :loading="loading">
            查询告警
          </NButton>
          
          <NButton @click="exportAlertData" :disabled="alertData.length === 0">
            导出数据
          </NButton>
        </NSpace>
      </NSpace>
    </NCard>

    <!-- 批量操作 -->
    <NCard v-if="checkedRowKeys.length > 0" title="批量操作" class="mb-4">
      <NSpace>
        <span>已选择 {{ checkedRowKeys.length }} 条告警</span>
        
        <NButton type="info" @click="handleBatchProcess('PROCESSING')">
          批量设为处理中
        </NButton>
        
        <NButton type="success" @click="handleBatchProcess('PROCESSED')">
          批量设为已处理
        </NButton>
        
        <NButton type="warning" @click="handleBatchProcess('IGNORED')">
          批量忽略
        </NButton>
      </NSpace>
    </NCard>

    <!-- 告警数据表格 -->
    <NCard title="告警记录">
      <NDataTable
        :data="alertData"
        :columns="columns"
        :row-key="(row) => row.alertId"
        :loading="loading"
        v-model:checked-row-keys="checkedRowKeys"
        size="small"
        striped
        :pagination="{
          page: searchParams.pageNum,
          pageSize: searchParams.pageSize,
          itemCount: total,
          onUpdatePage: handlePageChange,
          onUpdatePageSize: handlePageSizeChange,
          showSizePicker: true,
          pageSizes: [20, 50, 100]
        }"
      />
    </NCard>
  </div>
</template>

<style scoped>
.geofence-alert-management {
  padding: 16px;
}

.stats-cards {
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  padding: 8px 16px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a73e8;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.label {
  font-weight: 500;
  color: #333;
  min-width: 80px;
  text-align: right;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>