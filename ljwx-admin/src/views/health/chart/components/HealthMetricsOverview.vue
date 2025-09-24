<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'HealthMetricsOverview'
});

interface Props {
  healthData: any;
  healthMetrics: any;
  metricsConfig: any;
  loading: boolean;
}

const props = defineProps<Props>();

const selectedPeriod = ref<'today' | 'week' | 'month'>('today');

// 主要指标图表
const { domRef: mainChartRef, updateOptions: updateMainChart } = useEcharts(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1,
    textStyle: {
      color: '#333'
    },
    formatter: (params: any) => {
      let content = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`;
      params.forEach((param: any) => {
        const config = props.metricsConfig[param.seriesName];
        content += `
          <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span style="margin-right: 12px;">${config?.name || param.seriesName}:</span>
            <span style="font-weight: 600;">${config?.format(param.value) || param.value}</span>
          </div>
        `;
      });
      return content;
    }
  },
  legend: {
    show: false
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: [],
    axisLine: {
      lineStyle: {
        color: '#e8e8e8'
      }
    },
    axisLabel: {
      color: '#8c8c8c',
      fontSize: 12
    }
  },
  yAxis: [
    {
      type: 'value',
      name: '心率 (bpm)',
      position: 'left',
      axisLine: {
        show: true,
        lineStyle: {
          color: '#FF6B6B'
        }
      },
      axisLabel: {
        color: '#FF6B6B',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: '#f5f5f5'
        }
      }
    },
    {
      type: 'value',
      name: '血氧 (%)',
      position: 'right',
      axisLine: {
        show: true,
        lineStyle: {
          color: '#4ECDC4'
        }
      },
      axisLabel: {
        color: '#4ECDC4',
        fontSize: 12
      }
    }
  ],
  series: []
}));

// 趋势对比图表
const { domRef: trendChartRef, updateOptions: updateTrendChart } = useEcharts(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1,
    textStyle: {
      color: '#333'
    }
  },
  legend: {
    top: '5%',
    left: 'center',
    textStyle: {
      fontSize: 12
    }
  },
  series: [
    {
      name: '健康指标分布',
      type: 'pie',
      radius: ['50%', '70%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '18',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: []
    }
  ]
}));

// 更新主图表
function updateMainChartData() {
  if (!props.healthData.timestamps.length) return;

  const series = [];
  
  // 心率曲线
  if (props.healthData.heartRate.length > 0) {
    series.push({
      name: 'heart_rate',
      type: 'line',
      yAxisIndex: 0,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#FF6B6B'
      },
      itemStyle: {
        color: '#FF6B6B'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
            { offset: 1, color: 'rgba(255, 107, 107, 0.05)' }
          ]
        }
      },
      data: props.healthData.heartRate
    });
  }

  // 血氧曲线
  if (props.healthData.bloodOxygen.length > 0) {
    series.push({
      name: 'blood_oxygen',
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#4ECDC4'
      },
      itemStyle: {
        color: '#4ECDC4'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(78, 205, 196, 0.3)' },
            { offset: 1, color: 'rgba(78, 205, 196, 0.05)' }
          ]
        }
      },
      data: props.healthData.bloodOxygen
    });
  }

  updateMainChart(opts => {
    opts.xAxis.data = props.healthData.timestamps;
    opts.series = series;
    return opts;
  });
}

// 更新趋势图表
function updateTrendChartData() {
  const statusCounts = {
    normal: 0,
    warning: 0,
    danger: 0
  };

  Object.values(props.healthMetrics.status).forEach((status: any) => {
    if (status in statusCounts) {
      statusCounts[status as keyof typeof statusCounts]++;
    }
  });

  const pieData = [
    { 
      value: statusCounts.normal, 
      name: '正常', 
      itemStyle: { color: '#52c41a' } 
    },
    { 
      value: statusCounts.warning, 
      name: '警告', 
      itemStyle: { color: '#faad14' } 
    },
    { 
      value: statusCounts.danger, 
      name: '异常', 
      itemStyle: { color: '#f5222d' } 
    }
  ].filter(item => item.value > 0);

  updateTrendChart(opts => {
    opts.series[0].data = pieData;
    return opts;
  });
}

// 监听数据变化
watch(() => props.healthData, updateMainChartData, { deep: true, immediate: true });
watch(() => props.healthMetrics, updateTrendChartData, { deep: true, immediate: true });

// 计算平均值数据
const averageMetrics = computed(() => {
  const metrics = [];
  Object.keys(props.metricsConfig).forEach(key => {
    const current = props.healthMetrics.current[key];
    const average = props.healthMetrics.average[key];
    const config = props.metricsConfig[key];
    
    if (current !== undefined && average !== undefined) {
      metrics.push({
        key,
        name: config.name,
        current,
        average,
        difference: current - average,
        unit: config.unit,
        color: config.color,
        status: props.healthMetrics.status[key]
      });
    }
  });
  return metrics;
});
</script>

<template>
  <div class="health-metrics-overview">
    <!-- 主要生命体征图表 -->
    <NCard title="主要生命体征趋势" class="main-chart-card">
      <template #header-extra>
        <NButtonGroup size="small">
          <NButton 
            :type="selectedPeriod === 'today' ? 'primary' : 'default'"
            @click="selectedPeriod = 'today'"
          >
            今日
          </NButton>
          <NButton 
            :type="selectedPeriod === 'week' ? 'primary' : 'default'"
            @click="selectedPeriod = 'week'"
          >
            本周
          </NButton>
          <NButton 
            :type="selectedPeriod === 'month' ? 'primary' : 'default'"
            @click="selectedPeriod = 'month'"
          >
            本月
          </NButton>
        </NButtonGroup>
      </template>
      
      <NSpin :show="loading">
        <div ref="mainChartRef" class="main-chart"></div>
      </NSpin>
    </NCard>

    <!-- 辅助信息区域 -->
    <div class="metrics-sidebar">
      <!-- 健康指标分布 -->
      <NCard title="健康指标分布" class="distribution-card">
        <div ref="trendChartRef" class="trend-chart"></div>
      </NCard>

      <!-- 平均值对比 -->
      <NCard title="当前值 vs 平均值" class="comparison-card">
        <div class="comparison-list">
          <div 
            v-for="metric in averageMetrics.slice(0, 6)" 
            :key="metric.key"
            class="comparison-item"
          >
            <div class="metric-header">
              <div class="metric-info">
                <NIcon :color="metric.color" size="16">
                  <i :class="metricsConfig[metric.key].icon"></i>
                </NIcon>
                <span class="metric-name">{{ metric.name }}</span>
              </div>
              <NTag 
                :type="metric.status === 'normal' ? 'success' : 
                       metric.status === 'warning' ? 'warning' : 'error'"
                size="small"
              >
                {{ metric.status === 'normal' ? '正常' : 
                   metric.status === 'warning' ? '注意' : '异常' }}
              </NTag>
            </div>
            <div class="metric-values">
              <div class="value-item">
                <span class="label">当前</span>
                <span class="value current">{{ metricsConfig[metric.key].format(metric.current) }}</span>
              </div>
              <div class="value-item">
                <span class="label">平均</span>
                <span class="value average">{{ metricsConfig[metric.key].format(metric.average) }}</span>
              </div>
              <div class="value-item">
                <span class="label">差值</span>
                <span 
                  class="value difference"
                  :class="{ 
                    positive: metric.difference > 0, 
                    negative: metric.difference < 0 
                  }"
                >
                  {{ metric.difference > 0 ? '+' : '' }}{{ metricsConfig[metric.key].format(metric.difference) }}
                </span>
              </div>
            </div>
          </div>
          
          <div v-if="averageMetrics.length === 0" class="no-data">
            <NEmpty description="暂无健康数据" />
          </div>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.health-metrics-overview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  height: 100%;
}

.main-chart-card {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.main-chart {
  height: 400px;
  width: 100%;
}

.metrics-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.distribution-card,
.comparison-card {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.trend-chart {
  height: 200px;
  width: 100%;
}

.comparison-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.comparison-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 4px solid transparent;
}

.comparison-item:hover {
  background: #f0f0f0;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.metric-values {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.value-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.value-item .label {
  font-size: 11px;
  color: #8c8c8c;
}

.value-item .value {
  font-size: 12px;
  font-weight: 600;
}

.value.current {
  color: #1890ff;
}

.value.average {
  color: #52c41a;
}

.value.difference.positive {
  color: #f5222d;
}

.value.difference.negative {
  color: #52c41a;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .health-metrics-overview {
    grid-template-columns: 1fr;
  }
  
  .metrics-sidebar {
    flex-direction: row;
  }
}

@media (max-width: 768px) {
  .metrics-sidebar {
    flex-direction: column;
  }
  
  .metric-values {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>