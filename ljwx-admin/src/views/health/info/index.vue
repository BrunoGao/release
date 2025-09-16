<script setup lang="tsx">
import { NCard, NSpace, NButton, NDataTable, NSkeleton, NTag, NTooltip, NProgress, NEmpty } from 'naive-ui';
import { ref, onMounted, watch, computed, h } from 'vue';
import { fetchGetHealthDataBasicList, fetchGetHealthAnalytics, fetchGetSleepAnalytics, fetchGetExerciseAnalytics } from '@/service/api';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import { convertToBeijingTime } from '@/utils/date';

import UserHealthDataSearch from './modules/user-health-data-search.vue';
import HealthAnalyticsCharts from './components/HealthAnalyticsCharts.vue';

defineOptions({
  name: 'HealthInfoPage'
});

const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 基础状态
const loading = ref(false);
const tableData = ref<any[]>([]);
const selectedUserIds = ref<string[]>([]);
const selectedRows = ref<any[]>([]);

// 健康数据分析数据（从统一API获取）
const healthAnalyticsData = ref<any>(null);

// 搜索参数
const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const searchParams = ref({
  page: 1,
  pageSize: 20,
  customerId,
  orgId: null,
  userId: null,
  startDate,
  endDate
});

// 分页状态
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  onChange: (page: number) => {
    pagination.value.page = page;
    searchParams.value.page = page;
    loadHealthData();
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize;
    pagination.value.page = 1;
    searchParams.value.page = 1;
    searchParams.value.pageSize = pageSize;
    loadHealthData();
  }
});

// 加载健康数据
const loadHealthData = async () => {
  loading.value = true;
  
  try {
    const response = await fetchGetHealthDataBasicList(searchParams.value);
    
    if (response.data) {
      // 基础表格数据
      tableData.value = response.data.records || [];
      pagination.value.total = response.data.total || 0;
      
      // 保存完整的健康分析数据（包含图表数据）
      healthAnalyticsData.value = {
        basicData: response.data.records || [],
        sleepData: response.data.sleepData || [],
        workoutData: response.data.workoutData || [],
        scientificSleepData: response.data.scientificSleepData || [],
        exerciseDailyData: response.data.exerciseDailyData || [],
        exerciseWeekData: response.data.exerciseWeekData || [],
        records: response.data.records || [], // 基础数据记录，用于心血管和活动量图表
        supportedFields: response.data.supportedFields || {}
      };
      
      console.log('加载健康数据成功:', {
        表格数据: tableData.value.length,
        睡眠数据: healthAnalyticsData.value.sleepData.length,
        运动数据: healthAnalyticsData.value.workoutData.length,
        科学睡眠: healthAnalyticsData.value.scientificSleepData.length,
        日常运动: healthAnalyticsData.value.exerciseDailyData.length,
        周运动: healthAnalyticsData.value.exerciseWeekData.length
      });
    } else {
      tableData.value = [];
      pagination.value.total = 0;
      healthAnalyticsData.value = null;
    }
  } catch (error) {
    console.error('加载健康数据失败:', error);
    tableData.value = [];
    pagination.value.total = 0;
    healthAnalyticsData.value = null;
  } finally {
    loading.value = false;
  }
};

// 表格列配置
const columns = computed(() => [
  {
    type: 'selection',
    key: 'selection',
    width: 50,
    fixed: 'left'
  },
  {
    key: 'id',
    title: 'ID',
    align: 'center',
    width: 80,
    render: (row: any) => h(NTag, { size: 'small', type: 'info' }, { default: () => row.id })
  },
  {
    key: 'orgName',
    title: '部门名称',
    align: 'center',
    width: 150,
    render: (row: any) => row.orgName || '-'
  },
  {
    key: 'userName',
    title: '员工名称',
    align: 'center',
    width: 120,
    render: (row: any) => {
      const name = row.userName || '未知员工';
      return h(NTag, { 
        size: 'small', 
        type: name === '未知员工' ? 'warning' : 'success' 
      }, { default: () => name });
    }
  },
  {
    key: 'deviceSn',
    title: '设备序列号',
    align: 'center',
    width: 120,
    render: (row: any) => {
      if (!row.deviceSn) return '-';
      return h(NTooltip, {
        trigger: 'hover'
      }, {
        trigger: () => h('span', { 
          class: 'cursor-pointer text-blue-600 font-mono text-sm' 
        }, row.deviceSn.substring(0, 8) + '...'),
        default: () => row.deviceSn
      });
    }
  },
  // 生理指标列
  {
    key: 'vitalSigns',
    title: '生理指标',
    align: 'center',
    width: 300,
    render: (row: any) => {
      const indicators = [];
      
      // 心率
      if (row.heartRate) {
        const color = getHeartRateColor(row.heartRate);
        indicators.push(
          h(NTag, { 
            size: 'small', 
            color: { color, textColor: '#fff' },
            class: 'mr-1 mb-1'
          }, { 
            default: () => `❤️ ${row.heartRate}bpm` 
          })
        );
      }
      
      // 血氧
      if (row.bloodOxygen) {
        const color = getBloodOxygenColor(row.bloodOxygen);
        indicators.push(
          h(NTag, { 
            size: 'small', 
            color: { color, textColor: '#fff' },
            class: 'mr-1 mb-1'
          }, { 
            default: () => `🫁 ${row.bloodOxygen}%` 
          })
        );
      }
      
      // 血压
      if (row.pressureHigh && row.pressureLow) {
        const color = getBloodPressureColor(row.pressureHigh, row.pressureLow);
        indicators.push(
          h(NTag, { 
            size: 'small', 
            color: { color, textColor: '#fff' },
            class: 'mr-1 mb-1'
          }, { 
            default: () => `🩸 ${row.pressureHigh}/${row.pressureLow}` 
          })
        );
      }
      
      // 体温
      if (row.temperature) {
        const color = getTemperatureColor(row.temperature);
        indicators.push(
          h(NTag, { 
            size: 'small', 
            color: { color, textColor: '#fff' },
            class: 'mr-1 mb-1'
          }, { 
            default: () => `🌡️ ${row.temperature}°C` 
          })
        );
      }
      
      return h('div', { class: 'flex flex-wrap' }, indicators);
    }
  },
  // 活动指标列
  {
    key: 'activityMetrics',
    title: '活动指标',
    align: 'center',
    width: 250,
    render: (row: any) => {
      const metrics = [];
      
      // 步数
      if (row.step) {
        const progress = Math.min(row.step / 10000 * 100, 100);
        metrics.push(
          h('div', { class: 'mb-2' }, [
            h('div', { class: 'flex items-center gap-2 mb-1' }, [
              h('span', { class: 'text-xs text-gray-600' }, '🚶 步数'),
              h('span', { class: 'text-sm font-medium' }, row.step.toLocaleString())
            ]),
            h(NProgress, {
              percentage: progress,
              color: progress >= 80 ? '#52c41a' : progress >= 60 ? '#faad14' : '#ff4d4f',
              height: 4
            })
          ])
        );
      }
      
      // 卡路里和距离
      const secondRow = [];
      if (row.calorie) {
        secondRow.push(
          h(NTag, { 
            size: 'small', 
            type: 'warning',
            class: 'mr-1'
          }, { 
            default: () => `🔥 ${row.calorie}kcal` 
          })
        );
      }
      if (row.distance) {
        secondRow.push(
          h(NTag, { 
            size: 'small', 
            type: 'info',
            class: 'mr-1'
          }, { 
            default: () => `📏 ${row.distance}km` 
          })
        );
      }
      
      if (secondRow.length > 0) {
        metrics.push(h('div', { class: 'flex flex-wrap' }, secondRow));
      }
      
      return h('div', { class: 'w-full' }, metrics);
    }
  },
  // 位置信息
  {
    key: 'coordinates',
    title: '位置信息',
    align: 'center',
    width: 180,
    render: (row: any) => {
      if (!row.latitude || !row.longitude) return '-';
      
      const coordStr = `${row.latitude.toFixed(4)}, ${row.longitude.toFixed(4)}`;
      return h(NTooltip, {
        trigger: 'hover'
      }, {
        trigger: () => h('span', { 
          class: 'cursor-pointer text-blue-600 font-mono text-xs' 
        }, coordStr),
        default: () => h('div', {}, [
          h('div', {}, `纬度: ${row.latitude}`),
          h('div', {}, `经度: ${row.longitude}`),
          row.altitude ? h('div', {}, `海拔: ${row.altitude}m`) : null
        ])
      });
    }
  },
  // 时间戳列 - 移到最后
  {
    key: 'timestamp',
    title: '时间戳',
    align: 'center',
    width: 160,
    render: (row: any) => convertToBeijingTime(row.timestamp)
  }
]);

// 颜色判断函数
const getHeartRateColor = (heartRate: number) => {
  if (heartRate < 60) return '#fa541c'; // 过低-橙红
  if (heartRate <= 100) return '#52c41a'; // 正常-绿色
  if (heartRate <= 140) return '#faad14'; // 偏高-黄色
  return '#f5222d'; // 过高-红色
};

const getBloodOxygenColor = (oxygen: number) => {
  if (oxygen >= 95) return '#52c41a'; // 正常-绿色
  if (oxygen >= 90) return '#faad14'; // 偏低-黄色
  return '#f5222d'; // 危险-红色
};

const getBloodPressureColor = (systolic: number, diastolic: number) => {
  if (systolic <= 120 && diastolic <= 80) return '#52c41a'; // 正常-绿色
  if (systolic <= 140 && diastolic <= 90) return '#faad14'; // 偏高-黄色
  return '#f5222d'; // 高血压-红色
};

const getTemperatureColor = (temp: number) => {
  if (temp >= 36.1 && temp <= 37.2) return '#52c41a'; // 正常-绿色
  if (temp < 36.1) return '#1890ff'; // 偏低-蓝色
  if (temp <= 38.0) return '#faad14'; // 偏高-黄色
  return '#f5222d'; // 发热-红色
};

// 处理表格行选择
const handleRowSelection = (keys: string[], rows: any[]) => {
  selectedRows.value = rows;
  selectedUserIds.value = rows.map(row => row.userId).filter(Boolean);
  
  console.log('选择的用户:', selectedUserIds.value);
};

// 获取用于图表分析的用户ID列表
const getAnalyticsUserIds = () => {
  // 如果用户在搜索条件中指定了特定用户，使用该用户
  if (searchParams.value.userId) {
    return [searchParams.value.userId];
  }
  
  // 否则使用当前表格中所有用户的ID
  const userIds = tableData.value
    .map(row => row.userId)
    .filter(Boolean)
    .filter((id, index, arr) => arr.indexOf(id) === index); // 去重
    
  console.log('图表分析用户ID:', userIds);
  return userIds;
};

// 统计信息
const statistics = computed(() => {
  if (!tableData.value || tableData.value.length === 0) {
    return {
      totalRecords: 0,
      avgHeartRate: 0,
      avgBloodOxygen: 0,
      totalSteps: 0,
      totalCalories: 0,
      healthyCount: 0,
      abnormalCount: 0
    };
  }
  
  const records = tableData.value;
  const validHeartRates = records.filter(r => r.heartRate).map(r => r.heartRate);
  const validBloodOxygen = records.filter(r => r.bloodOxygen).map(r => r.bloodOxygen);
  const totalSteps = records.reduce((sum, r) => sum + (r.step || 0), 0);
  const totalCalories = records.reduce((sum, r) => sum + (r.calorie || 0), 0);
  
  // 简单健康评估（心率60-100且血氧>=95为健康）
  const healthyCount = records.filter(r => 
    r.heartRate >= 60 && r.heartRate <= 100 && r.bloodOxygen >= 95
  ).length;
  
  return {
    totalRecords: records.length,
    avgHeartRate: validHeartRates.length > 0 
      ? Math.round(validHeartRates.reduce((a, b) => a + b, 0) / validHeartRates.length) 
      : 0,
    avgBloodOxygen: validBloodOxygen.length > 0 
      ? Math.round(validBloodOxygen.reduce((a, b) => a + b, 0) / validBloodOxygen.length) 
      : 0,
    totalSteps,
    totalCalories: Math.round(totalCalories),
    healthyCount,
    abnormalCount: records.length - healthyCount
  };
});

// 搜索处理
const handleSearch = () => {
  pagination.value.page = 1;
  searchParams.value.page = 1;
  loadHealthData();
};

const resetSearchParams = () => {
  searchParams.value = {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    startDate,
    endDate
  };
  pagination.value.page = 1;
  loadHealthData();
};

// 导出健康数据
const exportHealthData = () => {
  if (tableData.value.length === 0) {
    window.$message?.warning('暂无数据可导出');
    return;
  }
  
  try {
    // 构建CSV数据
    const headers = [
      'ID', '部门名称', '员工名称', '设备序列号', 
      '心率(bpm)', '血氧(%)', '体温(°C)', '收缩压', '舒张压', 
      '压力', '步数', '卡路里', '距离(km)', 
      '纬度', '经度', '海拔(m)', '时间戳'
    ];
    
    const csvData = tableData.value.map(row => [
      row.id || '',
      row.orgName || '',
      row.userName || '',
      row.deviceSn || '',
      row.heartRate || '',
      row.bloodOxygen || '',
      row.temperature || '',
      row.pressureHigh || '',
      row.pressureLow || '',
      row.stress || '',
      row.step || '',
      row.calorie || '',
      row.distance || '',
      row.latitude || '',
      row.longitude || '',
      row.altitude || '',
      convertToBeijingTime(row.timestamp) || ''
    ]);
    
    // 添加表头
    csvData.unshift(headers);
    
    // 转换为CSV格式
    const csvContent = csvData.map(row => 
      row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    // 添加BOM以支持中文
    const bom = '\ufeff';
    const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // 生成文件名
    const now = new Date();
    const fileName = `健康数据_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}.csv`;
    
    // 下载文件
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    
    window.$message?.success(`导出成功：${fileName}`);
    console.log('✅ 健康数据导出完成:', fileName, `${tableData.value.length}条记录`);
    
  } catch (error) {
    console.error('❌ 健康数据导出失败:', error);
    window.$message?.error('导出失败，请重试');
  }
};

// 组织和用户选项
const orgUnitsTree = ref<any[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  const { error, data: treeData } = await fetchGetOrgUnitsTree(customerId);
  if (!error && treeData) {
    orgUnitsTree.value = treeData;
    // 初始化时获取第一个部门的员工列表
    if (treeData.length > 0) {
      const result = await handleBindUsersByOrgId(treeData[0].id);
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
}

// 监听部门变化，更新员工列表
watch(
  () => searchParams.value.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

onMounted(() => {
  handleInitOptions();
  loadHealthData();
});
</script>

<template>
  <div class="health-info-container">
    <!-- 搜索条件 -->
    <UserHealthDataSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @reset="resetSearchParams"
      @search="handleSearch"
    />
    
    <!-- 统计概览卡片 -->
    <NCard :bordered="false" class="mb-4">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="text-lg font-medium">📊 数据概览</span>
          <NTag v-if="selectedRows.length > 0" type="primary" size="small">
            已选择 {{ selectedRows.length }} 条记录
          </NTag>
        </div>
      </template>
      
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <!-- 记录总数 -->
        <div class="text-center p-3 bg-blue-50 rounded-lg">
          <div class="text-xl font-bold text-blue-600">{{ statistics.totalRecords }}</div>
          <div class="text-xs text-blue-500 mt-1">总记录数</div>
        </div>
        
        <!-- 平均心率 -->
        <div class="text-center p-3 bg-red-50 rounded-lg">
          <div class="text-xl font-bold text-red-600">{{ statistics.avgHeartRate }}</div>
          <div class="text-xs text-red-500 mt-1">平均心率(bpm)</div>
        </div>
        
        <!-- 平均血氧 -->
        <div class="text-center p-3 bg-green-50 rounded-lg">
          <div class="text-xl font-bold text-green-600">{{ statistics.avgBloodOxygen }}%</div>
          <div class="text-xs text-green-500 mt-1">平均血氧</div>
        </div>
        
        <!-- 总步数 -->
        <div class="text-center p-3 bg-purple-50 rounded-lg">
          <div class="text-xl font-bold text-purple-600">{{ statistics.totalSteps.toLocaleString() }}</div>
          <div class="text-xs text-purple-500 mt-1">总步数</div>
        </div>
        
        <!-- 总卡路里 -->
        <div class="text-center p-3 bg-orange-50 rounded-lg">
          <div class="text-xl font-bold text-orange-600">{{ statistics.totalCalories }}</div>
          <div class="text-xs text-orange-500 mt-1">总卡路里</div>
        </div>
        
        <!-- 健康记录 -->
        <div class="text-center p-3 bg-green-50 rounded-lg">
          <div class="text-xl font-bold text-green-600">{{ statistics.healthyCount }}</div>
          <div class="text-xs text-green-500 mt-1">健康记录</div>
        </div>
        
        <!-- 异常记录 -->
        <div class="text-center p-3 bg-red-50 rounded-lg">
          <div class="text-xl font-bold text-red-600">{{ statistics.abnormalCount }}</div>
          <div class="text-xs text-red-500 mt-1">异常记录</div>
        </div>
      </div>
    </NCard>

    <!-- 健康数据表格 -->
    <NCard :bordered="false" class="card-wrapper mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">🏥 健康数据表格</span>
          <div class="flex items-center gap-2">
            <NTag v-if="loading" type="warning" size="small">
              加载中...
            </NTag>
            <NButton 
              size="small" 
              @click="loadHealthData()" 
              :loading="loading"
            >
              刷新数据
            </NButton>
            <NButton 
              size="small" 
              type="primary"
              @click="exportHealthData()"
              :disabled="loading || tableData.length === 0"
            >
              导出数据
            </NButton>
          </div>
        </div>
      </template>
      
      <!-- 骨架屏加载状态 -->
      <div v-if="loading" class="space-y-4">
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
      </div>
      
      <!-- 空数据状态 -->
      <NEmpty v-else-if="tableData.length === 0" description="暂无健康数据" />
      
      <!-- 数据表格 -->
      <NDataTable
        v-else
        :scroll-x="1400"
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        @update:checked-row-keys="handleRowSelection"
        class="health-data-table-content"
      />
    </NCard>

    <!-- 专业图表分析 -->
    <div v-if="healthAnalyticsData && tableData.length > 0">
      <HealthAnalyticsCharts
        :health-data="healthAnalyticsData"
        :visible="true"
      />
    </div>
    
    <!-- 无数据提示 -->
    <NCard v-else-if="!loading" :bordered="false" class="text-center py-8">
      <NEmpty description="暂无健康数据，无法生成图表分析" />
    </NCard>
  </div>
</template>

<style scoped>
.health-info-container {
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background-color: #f5f5f5;
}

.health-data-table-content {
  /* 自定义表格样式 */
  :deep(.n-data-table-th) {
    background-color: #f8fafc;
    font-weight: 600;
  }
  
  :deep(.n-data-table-td) {
    border-bottom: 1px solid #f0f0f0;
  }
  
  :deep(.n-data-table-tr:hover .n-data-table-td) {
    background-color: #f0f9ff;
  }
}

/* 卡片容器样式 */
.card-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 确保表格容器可以滚动 */
.card-wrapper :deep(.n-card__content) {
  max-height: 600px;
  overflow: auto;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .health-info-container {
    padding: 8px;
  }
  
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .card-wrapper :deep(.n-card__content) {
    max-height: 400px;
  }
}

@media (max-width: 480px) {
  .health-info-container {
    padding: 4px;
  }
  
  .grid {
    grid-template-columns: 1fr;
  }
  
  .card-wrapper :deep(.n-card__content) {
    max-height: 300px;
  }
}

/* 滚动条样式优化 */
.health-info-container::-webkit-scrollbar {
  width: 6px;
}

.health-info-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.health-info-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.health-info-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 表格内部滚动条样式 */
.card-wrapper :deep(.n-card__content)::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.card-wrapper :deep(.n-card__content)::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.card-wrapper :deep(.n-card__content)::-webkit-scrollbar-thumb {
  background: #d1d1d1;
  border-radius: 2px;
}
</style>