<script setup lang="tsx">
import { NButton, NTooltip, NTag, NCard, NSpace, NProgress, NSkeleton, NDataTable } from 'naive-ui';
import { type Ref, h, ref, onMounted, watch, computed } from 'vue';
import { fetchGetHealthDataBasicList } from '@/service/api';
import { convertToBeijingTime } from '@/utils/date';

interface Props {
  searchParams?: Record<string, any>;
  selectedUserIds?: string[];
  loading?: boolean;
}

interface Emits {
  (e: 'row-select', userIds: string[]): void;
  (e: 'data-change', data: any[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  searchParams: () => ({}),
  selectedUserIds: () => [],
  loading: false
});

const emit = defineEmits<Emits>();

// 表格行选择状态
const selectedRows = ref<any[]>([]);
const rowKeys = ref<string[]>([]);

// 表格数据状态
const data = ref<any[]>([]);
const loading = ref(false);
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  onChange: (page: number) => {
    pagination.value.page = page;
    loadTableData();
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize;
    pagination.value.page = 1;
    loadTableData();
  }
});

// 加载表格数据
const loadTableData = async () => {
  if (props.loading) return;
  
  loading.value = true;
  
  try {
    const params = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      ...props.searchParams
    };
    
    const response = await fetchGetHealthDataBasicList(params);
    
    if (response.data) {
      data.value = response.data.records || [];
      pagination.value.total = response.data.total || 0;
      
      // 通知父组件数据变化
      emit('data-change', data.value);
    }
  } catch (error) {
    console.error('加载健康数据失败:', error);
    data.value = [];
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
      render: row => h(NTag, { size: 'small', type: 'info' }, { default: () => row.id })
    },
    {
      key: 'userName',
      title: '用户名称',
      align: 'center',
      width: 120,
      render: row => {
        const name = row.userName || '未知用户';
        return h(NTag, { 
          size: 'small', 
          type: name === '未知用户' ? 'warning' : 'success' 
        }, { default: () => name });
      }
    },
    {
      key: 'orgName',
      title: '部门名称',
      align: 'center',
      width: 150,
      render: row => row.orgName || '-'
    },
    {
      key: 'deviceSn',
      title: '设备序列号',
      align: 'center',
      width: 120,
      render: row => {
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
    {
      key: 'timestamp',
      title: '时间戳',
      align: 'center',
      width: 160,
      render: row => convertToBeijingTime(row.timestamp)
    },
    // ========== 生理指标列 ==========
    {
      key: 'vitalSigns',
      title: '生理指标',
      align: 'center',
      width: 300,
      render: row => {
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
    // ========== 活动指标列 ==========
    {
      key: 'activityMetrics',
      title: '活动指标',
      align: 'center',
      width: 250,
      render: row => {
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
    // ========== 位置信息 ==========
    {
      key: 'coordinates',
      title: '位置信息',
      align: 'center',
      width: 180,
      render: row => {
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
    // ========== 操作列 ==========
    {
      key: 'actions',
      title: '操作',
      align: 'center',
      width: 100,
      fixed: 'right',
      render: row => {
        return h(NSpace, { size: 'small' }, {
          default: () => [
            h(NButton, {
              size: 'small',
              type: 'primary',
              ghost: true,
              onClick: () => handleViewAnalytics(row)
            }, { default: () => '查看分析' })
          ]
        });
      }
    }
  ]
);

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

// 统计信息计算
const statistics = computed(() => {
  if (!data.value || data.value.length === 0) {
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
  
  const records = data.value;
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

// 事件处理
const handleViewAnalytics = (row: any) => {
  const userIds = [row.userId];
  emit('row-select', userIds);
};

const handleRowSelection = (keys: string[], rows: any[]) => {
  rowKeys.value = keys;
  selectedRows.value = rows;
  
  const userIds = rows.map(row => row.userId).filter(Boolean);
  emit('row-select', userIds);
};

// 外部搜索参数变化时重新加载
watch(() => props.searchParams, (newParams) => {
  if (newParams) {
    loadTableData();
  }
}, { deep: true });

// 数据变化时通知父组件
watch(data, (newData) => {
  emit('data-change', newData || []);
}, { deep: true });

onMounted(() => {
  getDataByPage();
});

// 暴露方法给父组件
defineExpose({
  refresh: getDataByPage,
  resetSearch: resetSearchParams,
  getSelectedRows: () => selectedRows.value,
  clearSelection: () => {
    rowKeys.value = [];
    selectedRows.value = [];
  }
});
</script>

<template>
  <div class="health-data-table">
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

    <!-- 数据表格 -->
    <NCard :bordered="false" class="card-wrapper">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">🏥 健康数据表格</span>
          <div class="flex items-center gap-2">
            <NTag v-if="props.loading || loading" type="warning" size="small">
              加载中...
            </NTag>
            <NButton 
              size="small" 
              @click="loadTableData()" 
              :loading="loading"
            >
              刷新数据
            </NButton>
          </div>
        </div>
      </template>
      
      <!-- 骨架屏加载状态 -->
      <div v-if="props.loading || loading" class="space-y-4">
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
        <NSkeleton height="40px" :sharp="false" />
      </div>
      
      <!-- 数据表格 -->
      <NDataTable
        v-else
        :scroll-x="1400"
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        :checked-row-keys="rowKeys"
        @update:checked-row-keys="handleRowSelection"
        class="health-data-table-content"
      />
    </NCard>
  </div>
</template>

<style scoped>
.health-data-table {
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
}

/* 响应式优化 */
@media (max-width: 768px) {
  .health-data-table {
    .grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 480px) {
  .health-data-table {
    .grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>