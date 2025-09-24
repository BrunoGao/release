<template>
  <div class="medical-chart">
    <div class="chart-header">
      <div class="chart-title">
        <h4>{{ chartConfig.title }}</h4>
        <p class="chart-subtitle">{{ chartConfig.subtitle }}</p>
      </div>
      <div class="chart-controls">
        <NSelect
          v-model:value="selectedTimeRange"
          :options="timeRangeOptions"
          size="small"
          style="width: 120px"
          @update:value="onTimeRangeChange"
        />
        <NButtonGroup size="small">
          <NButton 
            :type="chartType === 'line' ? 'primary' : 'default'"
            @click="setChartType('line')"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:show-chart"></i></NIcon>
            </template>
          </NButton>
          <NButton 
            :type="chartType === 'bar' ? 'primary' : 'default'"
            @click="setChartType('bar')"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:bar-chart"></i></NIcon>
            </template>
          </NButton>
          <NButton 
            :type="chartType === 'area' ? 'primary' : 'default'"
            @click="setChartType('area')"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:area-chart"></i></NIcon>
            </template>
          </NButton>
        </NButtonGroup>
      </div>
    </div>

    <!-- 统计摘要 -->
    <div class="chart-stats">
      <div class="stat-item">
        <span class="stat-label">最新值</span>
        <span class="stat-value" :class="getValueStatus(currentValue)">
          {{ formatValue(currentValue) }}
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均值</span>
        <span class="stat-value">{{ formatValue(averageValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最大值</span>
        <span class="stat-value">{{ formatValue(maxValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最小值</span>
        <span class="stat-value">{{ formatValue(minValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">变化趋势</span>
        <span class="stat-trend" :class="trendClass">
          <NIcon size="16">
            <i :class="trendIcon"></i>
          </NIcon>
          {{ trendText }}
        </span>
      </div>
    </div>

    <!-- 正常值范围指示器 -->
    <div class="normal-range-indicator" v-if="chartConfig.normalRange">
      <div class="range-bar">
        <div class="range-section danger-low"></div>
        <div class="range-section warning-low"></div>
        <div class="range-section normal"></div>
        <div class="range-section warning-high"></div>
        <div class="range-section danger-high"></div>
      </div>
      <div class="range-labels">
        <span class="range-label">{{ chartConfig.normalRange.min }}</span>
        <span class="range-label normal-label">正常范围</span>
        <span class="range-label">{{ chartConfig.normalRange.max }}</span>
      </div>
    </div>

    <!-- 主图表区域 -->
    <div class="chart-container">
      <div ref="chartRef" class="chart-canvas" :style="{ height: chartHeight + 'px' }"></div>
      
      <!-- 实时数据指示器 -->
      <div class="realtime-indicator" v-if="isRealtime">
        <div class="pulse-dot"></div>
        <span>实时监控中</span>
      </div>
    </div>

    <!-- 异常事件标记 -->
    <div class="event-markers" v-if="events.length">
      <div class="events-title">异常事件</div>
      <div class="events-list">
        <div 
          v-for="event in events" 
          :key="event.id"
          class="event-item"
          :class="event.type"
        >
          <div class="event-time">{{ formatTime(event.timestamp) }}</div>
          <div class="event-description">{{ event.description }}</div>
          <div class="event-value">{{ formatValue(event.value) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';

// Props定义
interface Props {
  data: number[];
  timestamps: string[];
  metric: string;
  loading?: boolean;
  height?: number;
  realtime?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: 300,
  realtime: false
});

// Emits定义
const emit = defineEmits<{
  'time-range-change': [value: string];
  'chart-type-change': [value: string];
}>();

// 响应式数据
const chartRef = ref<HTMLElement>();
const chartInstance = ref<echarts.ECharts>();
const selectedTimeRange = ref('24h');
const chartType = ref('line');
const chartHeight = computed(() => props.height);
const isRealtime = computed(() => props.realtime);

// 图表配置
const chartConfigs = {
  heart_rate: {
    title: '心率监测',
    subtitle: 'Heart Rate Monitoring',
    unit: 'bpm',
    color: '#f5222d',
    normalRange: { min: 60, max: 100 },
    dangerThresholds: { low: 50, high: 120 }
  },
  blood_oxygen: {
    title: '血氧饱和度',
    subtitle: 'Blood Oxygen Saturation',
    unit: '%',
    color: '#52c41a',
    normalRange: { min: 95, max: 100 },
    dangerThresholds: { low: 90, high: 100 }
  },
  temperature: {
    title: '体温监测',
    subtitle: 'Body Temperature',
    unit: '°C',
    color: '#faad14',
    normalRange: { min: 36.1, max: 37.2 },
    dangerThresholds: { low: 35.5, high: 38.0 }
  },
  pressure_high: {
    title: '收缩压',
    subtitle: 'Systolic Blood Pressure',
    unit: 'mmHg',
    color: '#1890ff',
    normalRange: { min: 90, max: 120 },
    dangerThresholds: { low: 80, high: 140 }
  },
  pressure_low: {
    title: '舒张压',
    subtitle: 'Diastolic Blood Pressure', 
    unit: 'mmHg',
    color: '#722ed1',
    normalRange: { min: 60, max: 80 },
    dangerThresholds: { low: 50, high: 90 }
  },
  step: {
    title: '步数统计',
    subtitle: 'Daily Steps Count',
    unit: '步',
    color: '#13c2c2',
    normalRange: { min: 6000, max: 10000 },
    dangerThresholds: { low: 3000, high: 15000 }
  }
};

const chartConfig = computed(() => chartConfigs[props.metric as keyof typeof chartConfigs] || chartConfigs.heart_rate);

// 时间范围选项
const timeRangeOptions = [
  { label: '最近1小时', value: '1h' },
  { label: '最近6小时', value: '6h' },
  { label: '最近24小时', value: '24h' },
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' }
];

// 计算统计值
const validData = computed(() => props.data.filter(val => val > 0));

const currentValue = computed(() => {
  const data = validData.value;
  return data.length > 0 ? data[data.length - 1] : 0;
});

const averageValue = computed(() => {
  const data = validData.value;
  return data.length > 0 ? Math.round(data.reduce((sum, val) => sum + val, 0) / data.length * 10) / 10 : 0;
});

const maxValue = computed(() => {
  const data = validData.value;
  return data.length > 0 ? Math.max(...data) : 0;
});

const minValue = computed(() => {
  const data = validData.value;
  return data.length > 0 ? Math.min(...data) : 0;
});

// 趋势分析
const trendAnalysis = computed(() => {
  const data = validData.value;
  if (data.length < 2) return { trend: 'stable', change: 0 };
  
  const recent = data.slice(-5);
  const earlier = data.slice(-10, -5);
  
  if (recent.length === 0 || earlier.length === 0) return { trend: 'stable', change: 0 };
  
  const recentAvg = recent.reduce((sum, val) => sum + val, 0) / recent.length;
  const earlierAvg = earlier.reduce((sum, val) => sum + val, 0) / earlier.length;
  
  const change = ((recentAvg - earlierAvg) / earlierAvg) * 100;
  
  if (Math.abs(change) < 5) return { trend: 'stable', change: 0 };
  return { trend: change > 0 ? 'up' : 'down', change: Math.abs(change) };
});

const trendClass = computed(() => {
  switch (trendAnalysis.value.trend) {
    case 'up': return 'trend-up';
    case 'down': return 'trend-down';
    default: return 'trend-stable';
  }
});

const trendIcon = computed(() => {
  switch (trendAnalysis.value.trend) {
    case 'up': return 'i-material-symbols:trending-up';
    case 'down': return 'i-material-symbols:trending-down';
    default: return 'i-material-symbols:trending-flat';
  }
});

const trendText = computed(() => {
  const analysis = trendAnalysis.value;
  switch (analysis.trend) {
    case 'up': return `上升 ${analysis.change.toFixed(1)}%`;
    case 'down': return `下降 ${analysis.change.toFixed(1)}%`;
    default: return '平稳';
  }
});

// 异常事件
const events = computed(() => {
  const eventList = [];
  const config = chartConfig.value;
  
  props.data.forEach((value, index) => {
    if (value > 0) {
      if (value < config.dangerThresholds.low) {
        eventList.push({
          id: `${index}-low`,
          timestamp: props.timestamps[index],
          type: 'danger',
          description: '数值过低',
          value
        });
      } else if (value > config.dangerThresholds.high) {
        eventList.push({
          id: `${index}-high`,
          timestamp: props.timestamps[index],
          type: 'danger',
          description: '数值过高',
          value
        });
      } else if (value < config.normalRange.min || value > config.normalRange.max) {
        eventList.push({
          id: `${index}-warning`,
          timestamp: props.timestamps[index],
          type: 'warning',
          description: '超出正常范围',
          value
        });
      }
    }
  });
  
  return eventList.slice(-5); // 只显示最近5个事件
});

// 工具函数
const formatValue = (value: number) => {
  if (value === 0) return '--';
  return `${value} ${chartConfig.value.unit}`;
};

const formatTime = (timestamp: string) => {
  if (!timestamp) return '';
  try {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return timestamp;
  }
};

const getValueStatus = (value: number) => {
  const config = chartConfig.value;
  
  if (value < config.dangerThresholds.low || value > config.dangerThresholds.high) {
    return 'danger';
  } else if (value < config.normalRange.min || value > config.normalRange.max) {
    return 'warning';
  }
  return 'normal';
};

// 图表操作
const setChartType = (type: string) => {
  chartType.value = type;
  emit('chart-type-change', type);
  nextTick(() => {
    initChart();
  });
};

const onTimeRangeChange = (value: string) => {
  emit('time-range-change', value);
};

// 图表初始化
const initChart = () => {
  if (!chartRef.value) return;
  
  // 销毁现有实例
  if (chartInstance.value) {
    chartInstance.value.dispose();
  }
  
  // 创建新实例
  chartInstance.value = echarts.init(chartRef.value);
  
  const config = chartConfig.value;
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e6f4ff',
      borderWidth: 1,
      textStyle: { color: '#1a1a1a' },
      formatter: (params: any) => {
        const param = params[0];
        const value = param.value;
        const timestamp = param.axisValue;
        const status = getValueStatus(value);
        const statusText = status === 'danger' ? '危险' : status === 'warning' ? '警告' : '正常';
        
        return `
          <div style="font-size: 14px; font-weight: 600;">${config.title}</div>
          <div style="margin: 8px 0;">
            <span style="color: ${config.color};">●</span>
            <span style="margin-left: 8px;">${formatValue(value)}</span>
            <span style="margin-left: 12px; padding: 2px 6px; background: ${status === 'danger' ? '#fff2f0' : status === 'warning' ? '#fff7e6' : '#f6ffed'}; color: ${status === 'danger' ? '#f5222d' : status === 'warning' ? '#faad14' : '#52c41a'}; border-radius: 4px; font-size: 12px;">${statusText}</span>
          </div>
          <div style="color: #666; font-size: 12px;">${timestamp}</div>
        `;
      }
    },
    legend: {
      show: false
    },
    grid: {
      top: 20,
      right: 30,
      bottom: 60,
      left: 60,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.timestamps,
      axisLine: {
        lineStyle: { color: '#e6f4ff' }
      },
      axisLabel: {
        color: '#666',
        fontSize: 12,
        formatter: (value: string) => {
          if (!value) return '';
          try {
            return new Date(value).toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit'
            });
          } catch {
            return value;
          }
        }
      },
      axisTick: {
        alignWithLabel: true,
        lineStyle: { color: '#e6f4ff' }
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: { color: '#e6f4ff' }
      },
      axisLabel: {
        color: '#666',
        fontSize: 12,
        formatter: (value: number) => `${value} ${config.unit}`
      },
      splitLine: {
        lineStyle: { 
          color: '#f0f2f5',
          type: 'dashed'
        }
      },
      // 添加正常值范围的标记线
      ...(config.normalRange && {
        markLine: {
          silent: true,
          data: [
            {
              yAxis: config.normalRange.min,
              lineStyle: { color: '#52c41a', type: 'dashed', width: 1 },
              label: { formatter: `正常下限: ${config.normalRange.min}${config.unit}`, position: 'insideEndTop' }
            },
            {
              yAxis: config.normalRange.max,
              lineStyle: { color: '#52c41a', type: 'dashed', width: 1 },
              label: { formatter: `正常上限: ${config.normalRange.max}${config.unit}`, position: 'insideEndBottom' }
            }
          ]
        }
      })
    },
    series: [
      {
        name: config.title,
        type: chartType.value,
        data: props.data,
        smooth: chartType.value === 'line',
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: (params: any) => {
            const value = params.value;
            const status = getValueStatus(value);
            return status === 'danger' ? '#f5222d' : status === 'warning' ? '#faad14' : config.color;
          }
        },
        lineStyle: {
          color: config.color,
          width: 2
        },
        areaStyle: chartType.value === 'area' ? {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: config.color + '40' },
              { offset: 1, color: config.color + '10' }
            ]
          }
        } : undefined,
        // 添加正常值范围的背景
        markArea: config.normalRange ? {
          silent: true,
          itemStyle: {
            color: 'rgba(82, 196, 26, 0.1)'
          },
          data: [[
            { yAxis: config.normalRange.min },
            { yAxis: config.normalRange.max }
          ]]
        } : undefined
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };
  
  chartInstance.value.setOption(option);
  
  // 响应式处理
  window.addEventListener('resize', handleResize);
};

const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
};

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart();
  });
});

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose();
  }
  window.removeEventListener('resize', handleResize);
});

// 监听数据变化
watch([() => props.data, () => props.timestamps], () => {
  nextTick(() => {
    initChart();
  });
}, { deep: true });
</script>

<style scoped>
.medical-chart {
  background: white;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
}

.chart-title h4 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.chart-subtitle {
  font-size: 13px;
  color: #666;
  margin: 0;
  font-style: italic;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-stats {
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fafbfc;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-value.normal {
  color: #52c41a;
}

.stat-value.warning {
  color: #faad14;
}

.stat-value.danger {
  color: #f5222d;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
}

.trend-up {
  color: #f5222d;
}

.trend-down {
  color: #52c41a;
}

.trend-stable {
  color: #666;
}

.normal-range-indicator {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.range-bar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.range-section {
  flex: 1;
}

.range-section.danger-low {
  background: #ff4d4f;
}

.range-section.warning-low {
  background: #faad14;
}

.range-section.normal {
  background: #52c41a;
  flex: 2;
}

.range-section.warning-high {
  background: #faad14;
}

.range-section.danger-high {
  background: #ff4d4f;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.range-label {
  font-size: 12px;
  color: #666;
}

.normal-label {
  font-weight: 600;
  color: #52c41a;
}

.chart-container {
  position: relative;
  padding: 16px 24px 24px;
}

.chart-canvas {
  width: 100%;
}

.realtime-indicator {
  position: absolute;
  top: 24px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #52c41a;
  font-weight: 500;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.event-markers {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafbfc;
}

.events-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
}

.event-item.danger {
  background: #fff2f0;
  border-left: 3px solid #f5222d;
}

.event-item.warning {
  background: #fff7e6;
  border-left: 3px solid #faad14;
}

.event-time {
  color: #666;
  font-family: monospace;
}

.event-description {
  color: #1a1a1a;
  font-weight: 500;
  flex: 1;
  margin: 0 12px;
}

.event-value {
  font-weight: 600;
  color: #1a1a1a;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .chart-stats {
    flex-wrap: wrap;
    gap: 16px 12px;
  }
  
  .stat-item {
    min-width: 80px;
  }
  
  .chart-container {
    padding: 12px 16px 16px;
  }
}
</style>