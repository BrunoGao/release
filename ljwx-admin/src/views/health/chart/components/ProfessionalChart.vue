<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'ProfessionalChart'
});

interface Props {
  healthData: any;
  activeMetric: string;
  metricsConfig: any;
  loading: boolean;
}

interface Emits {
  (e: 'metric-change', metric: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const chartType = ref<'line' | 'bar' | 'area'>('line');
const showAverage = ref(true);
const showNormalRange = ref(true);
const timeRange = ref<'day' | 'week' | 'month'>('day');

// 主图表
const { domRef: mainChartRef, updateOptions: updateMainChart } = useEcharts(() => ({
  title: {
    text: '',
    left: 'center',
    textStyle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: '#262626'
    }
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1,
    textStyle: {
      color: '#333'
    },
    axisPointer: {
      type: 'cross',
      crossStyle: {
        color: '#999'
      }
    },
    formatter: (params: any) => {
      const config = props.metricsConfig[props.activeMetric];
      let content = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`;
      
      params.forEach((param: any) => {
        if (param.seriesName === '正常范围') return;
        content += `
          <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <span style="width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span style="margin-right: 12px;">${param.seriesName}:</span>
            <span style="font-weight: 600;">${config?.format(param.value) || param.value}</span>
          </div>
        `;
      });
      return content;
    }
  },
  legend: {
    show: true,
    top: '10%',
    left: 'center',
    textStyle: {
      fontSize: 12
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '20%',
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
      fontSize: 12,
      rotate: 0
    }
  },
  yAxis: {
    type: 'value',
    name: '',
    nameTextStyle: {
      color: '#8c8c8c',
      fontSize: 12
    },
    axisLine: {
      show: true,
      lineStyle: {
        color: '#e8e8e8'
      }
    },
    axisLabel: {
      color: '#8c8c8c',
      fontSize: 12
    },
    splitLine: {
      lineStyle: {
        color: '#f5f5f5',
        type: 'dashed'
      }
    }
  },
  series: [],
  animation: true,
  animationDuration: 1000,
  animationEasing: 'cubicOut'
}));

// 对比图表
const { domRef: compareChartRef, updateOptions: updateCompareChart } = useEcharts(() => ({
  title: {
    text: '多指标对比分析',
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: '#262626'
    }
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1
  },
  legend: {
    show: true,
    top: '10%',
    left: 'center',
    textStyle: {
      fontSize: 11
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '25%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: [],
    axisLabel: {
      fontSize: 10
    }
  },
  yAxis: [
    {
      type: 'value',
      name: '归一化值',
      min: 0,
      max: 100,
      axisLabel: {
        fontSize: 10
      }
    }
  ],
  series: []
}));

// 更新主图表
function updateMainChartData() {
  if (!props.healthData.timestamps.length || !props.activeMetric) return;

  const config = props.metricsConfig[props.activeMetric];
  const data = props.healthData[props.activeMetric] || [];
  
  if (!config || !data.length) return;

  const series = [];
  const title = `${config.name} 专业分析图表`;

  // 主数据系列
  const mainSeries: any = {
    name: config.name,
    type: chartType.value,
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      width: 3,
      color: config.color
    },
    itemStyle: {
      color: config.color
    },
    data: data.filter(val => val > 0)
  };

  // 根据图表类型添加样式
  if (chartType.value === 'area') {
    mainSeries.areaStyle = {
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
    };
  }

  series.push(mainSeries);

  // 平均线
  if (showAverage.value) {
    const validData = data.filter(val => val > 0);
    const average = validData.reduce((sum, val) => sum + val, 0) / validData.length;
    
    series.push({
      name: '平均值',
      type: 'line',
      lineStyle: {
        type: 'dashed',
        width: 2,
        color: '#faad14'
      },
      itemStyle: {
        color: '#faad14'
      },
      symbol: 'none',
      data: new Array(data.length).fill(average)
    });
  }

  // 正常范围
  if (showNormalRange.value && config.normal) {
    series.push({
      name: '正常范围',
      type: 'line',
      lineStyle: {
        width: 0
      },
      areaStyle: {
        color: 'rgba(82, 196, 26, 0.1)'
      },
      symbol: 'none',
      data: new Array(data.length).fill(config.normal.max),
      stack: 'range'
    });

    series.push({
      name: '',
      type: 'line',
      lineStyle: {
        width: 0
      },
      areaStyle: {
        color: 'rgba(255, 255, 255, 1)'
      },
      symbol: 'none',
      data: new Array(data.length).fill(config.normal.min),
      stack: 'range'
    });
  }

  updateMainChart(opts => {
    opts.title.text = title;
    opts.xAxis.data = props.healthData.timestamps;
    opts.yAxis.name = `${config.name} (${config.unit})`;
    opts.series = series;
    return opts;
  });
}

// 更新对比图表
function updateCompareChartData() {
  if (!props.healthData.timestamps.length) return;

  const series = [];
  const importantMetrics = ['heart_rate', 'blood_oxygen', 'temperature', 'step'];

  importantMetrics.forEach(metricKey => {
    const data = props.healthData[metricKey];
    const config = props.metricsConfig[metricKey];
    
    if (data && data.length > 0 && config) {
      // 归一化数据到0-100范围
      const validData = data.filter(val => val > 0);
      const min = Math.min(...validData);
      const max = Math.max(...validData);
      const normalizedData = data.map(val => {
        if (val <= 0) return 0;
        return ((val - min) / (max - min)) * 100;
      });

      series.push({
        name: config.name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2,
          color: config.color
        },
        data: normalizedData
      });
    }
  });

  updateCompareChart(opts => {
    opts.xAxis.data = props.healthData.timestamps;
    opts.series = series;
    return opts;
  });
}

// 选择指标
function selectMetric(metricKey: string) {
  emit('metric-change', metricKey);
}

// 监听数据变化
watch(() => props.healthData, () => {
  updateMainChartData();
  updateCompareChartData();
}, { deep: true, immediate: true });

watch(() => props.activeMetric, updateMainChartData, { immediate: true });
watch(() => chartType.value, updateMainChartData);
watch(() => showAverage.value, updateMainChartData);
watch(() => showNormalRange.value, updateMainChartData);

// 计算统计信息
const statistics = computed(() => {
  const data = props.healthData[props.activeMetric] || [];
  const validData = data.filter(val => val > 0);
  
  if (validData.length === 0) {
    return {
      count: 0,
      min: 0,
      max: 0,
      average: 0,
      latest: 0,
      trend: 'stable'
    };
  }

  const min = Math.min(...validData);
  const max = Math.max(...validData);
  const average = validData.reduce((sum, val) => sum + val, 0) / validData.length;
  const latest = validData[validData.length - 1];
  
  // 计算趋势
  let trend = 'stable';
  if (validData.length >= 3) {
    const recent = validData.slice(-3).reduce((sum, val) => sum + val, 0) / 3;
    const earlier = validData.slice(0, -3).reduce((sum, val) => sum + val, 0) / Math.max(1, validData.length - 3);
    const change = ((recent - earlier) / earlier) * 100;
    
    if (change > 5) trend = 'up';
    else if (change < -5) trend = 'down';
  }

  return {
    count: validData.length,
    min,
    max,
    average,
    latest,
    trend
  };
});

// 获取指标状态
function getMetricStatus(value: number, metricKey: string) {
  const config = props.metricsConfig[metricKey];
  if (!config?.normal) return 'unknown';
  
  if (value >= config.normal.min && value <= config.normal.max) return 'normal';
  if (value < config.normal.min * 0.8 || value > config.normal.max * 1.2) return 'danger';
  return 'warning';
}
</script>

<template>
  <div class="professional-chart">
    <!-- 控制面板 -->
    <NCard class="control-panel">
      <div class="controls-grid">
        <!-- 指标选择 -->
        <div class="control-group">
          <label class="control-label">监测指标</label>
          <div class="metric-buttons">
            <NButton
              v-for="(config, key) in metricsConfig"
              :key="key"
              :type="activeMetric === key ? 'primary' : 'default'"
              size="small"
              @click="selectMetric(key)"
            >
              <template #icon>
                <NIcon :color="activeMetric === key ? '#fff' : config.color">
                  <i :class="config.icon"></i>
                </NIcon>
              </template>
              {{ config.name }}
            </NButton>
          </div>
        </div>

        <!-- 图表类型 -->
        <div class="control-group">
          <label class="control-label">图表类型</label>
          <NButtonGroup size="small">
            <NButton 
              :type="chartType === 'line' ? 'primary' : 'default'"
              @click="chartType = 'line'"
            >
              线图
            </NButton>
            <NButton 
              :type="chartType === 'area' ? 'primary' : 'default'"
              @click="chartType = 'area'"
            >
              面积图
            </NButton>
            <NButton 
              :type="chartType === 'bar' ? 'primary' : 'default'"
              @click="chartType = 'bar'"
            >
              柱图
            </NButton>
          </NButtonGroup>
        </div>

        <!-- 显示选项 -->
        <div class="control-group">
          <label class="control-label">显示选项</label>
          <NSpace>
            <NCheckbox v-model:checked="showAverage" size="small">
              显示平均线
            </NCheckbox>
            <NCheckbox v-model:checked="showNormalRange" size="small">
              显示正常范围
            </NCheckbox>
          </NSpace>
        </div>
      </div>
    </NCard>

    <!-- 统计信息 -->
    <NCard v-if="activeMetric" class="statistics-panel">
      <template #header>
        <div class="stats-header">
          <NIcon :color="metricsConfig[activeMetric]?.color" size="20">
            <i :class="metricsConfig[activeMetric]?.icon"></i>
          </NIcon>
          <span>{{ metricsConfig[activeMetric]?.name }} 统计信息</span>
        </div>
      </template>
      
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-label">数据点数</div>
          <div class="stat-value">{{ statistics.count }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最新值</div>
          <div class="stat-value current" :class="getMetricStatus(statistics.latest, activeMetric)">
            {{ metricsConfig[activeMetric]?.format(statistics.latest) }}
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-label">平均值</div>
          <div class="stat-value">{{ metricsConfig[activeMetric]?.format(statistics.average) }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最小值</div>
          <div class="stat-value">{{ metricsConfig[activeMetric]?.format(statistics.min) }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">最大值</div>
          <div class="stat-value">{{ metricsConfig[activeMetric]?.format(statistics.max) }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">趋势</div>
          <div class="stat-value trend">
            <NIcon 
              :color="
                statistics.trend === 'up' ? '#52c41a' : 
                statistics.trend === 'down' ? '#f5222d' : '#faad14'
              "
              size="16"
            >
              <i v-if="statistics.trend === 'up'" class="i-material-symbols:trending-up"></i>
              <i v-else-if="statistics.trend === 'down'" class="i-material-symbols:trending-down"></i>
              <i v-else class="i-material-symbols:trending-flat"></i>
            </NIcon>
            {{ statistics.trend === 'up' ? '上升' : statistics.trend === 'down' ? '下降' : '稳定' }}
          </div>
        </div>
      </div>
    </NCard>

    <!-- 图表区域 -->
    <div class="charts-container">
      <!-- 主图表 -->
      <NCard class="main-chart-container">
        <NSpin :show="loading">
          <div ref="mainChartRef" class="professional-main-chart"></div>
        </NSpin>
      </NCard>

      <!-- 对比图表 -->
      <NCard title="多指标归一化对比" class="compare-chart-container">
        <div ref="compareChartRef" class="professional-compare-chart"></div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.professional-chart {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: slideInFromBottom 0.8s ease-out;
}

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.control-panel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(25px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.control-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.03) 0%, rgba(255, 0, 170, 0.03) 100%);
  pointer-events: none;
}

.control-panel:hover {
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 30px rgba(0, 245, 255, 0.15);
}

.controls-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 32px;
  align-items: start;
  position: relative;
  z-index: 1;
  padding: 24px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-label {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  position: relative;
  padding-left: 20px;
}

.control-label::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 2px;
  background: linear-gradient(90deg, #00f5ff, #ff00aa);
  border-radius: 1px;
}

.metric-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.statistics-panel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(25px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.statistics-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.03) 0%, rgba(255, 0, 170, 0.03) 100%);
  pointer-events: none;
}

.statistics-panel:hover {
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 30px rgba(0, 245, 255, 0.15);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  position: relative;
  z-index: 1;
  letter-spacing: 0.5px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 24px;
  position: relative;
  z-index: 1;
  padding: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: center;
  padding: 16px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.05) 0%, rgba(255, 0, 170, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.stat-item:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.stat-item:hover::before {
  opacity: 1;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  position: relative;
  z-index: 1;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.stat-value.current.normal {
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.stat-value.current.warning {
  color: #ffaa00;
  text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
}

.stat-value.current.danger {
  color: #ff00aa;
  text-shadow: 0 0 10px rgba(255, 0, 170, 0.5);
}

.stat-value.trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 16px;
}

.charts-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 28px;
  animation: fadeInScale 0.8s ease-out;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.main-chart-container,
.compare-chart-container {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(25px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-chart-container::before,
.compare-chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.03) 0%, rgba(255, 0, 170, 0.03) 100%);
  pointer-events: none;
  z-index: 0;
}

.main-chart-container:hover,
.compare-chart-container:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 30px rgba(0, 245, 255, 0.15);
}

.main-chart-container:hover::before,
.compare-chart-container:hover::before {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.08) 0%, rgba(255, 0, 170, 0.08) 100%);
}

.professional-main-chart,
.professional-compare-chart {
  height: 500px;
  width: 100%;
  position: relative;
  z-index: 1;
  border-radius: 16px;
  overflow: visible;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(5px);
}

.professional-main-chart::before,
.professional-compare-chart::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 30% 20%, rgba(0, 245, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(255, 0, 170, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.main-chart-container:hover .professional-main-chart::before,
.compare-chart-container:hover .professional-compare-chart::before {
  opacity: 1;
}

/* 响应式设计增强 */
@media (max-width: 1400px) {
  .controls-grid {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 20px;
  }
  
  .metric-buttons {
    max-height: 120px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 245, 255, 0.3) transparent;
  }
  
  .metric-buttons::-webkit-scrollbar {
    width: 6px;
  }
  
  .metric-buttons::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }
  
  .metric-buttons::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #00f5ff, #ff00aa);
    border-radius: 3px;
  }
  
  .charts-container {
    gap: 20px;
  }
}

@media (max-width: 1200px) {
  .charts-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  
  .professional-main-chart,
  .professional-compare-chart {
    height: 450px;
  }
}

@media (max-width: 768px) {
  .professional-chart {
    gap: 20px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 16px;
  }
  
  .metric-buttons {
    gap: 6px;
    flex-direction: column;
    align-items: stretch;
  }
  
  .metric-buttons .n-button {
    justify-content: flex-start;
  }
  
  .professional-main-chart,
  .professional-compare-chart {
    height: 350px;
  }
  
  .charts-container {
    gap: 16px;
  }
  
  .main-chart-container,
  .compare-chart-container {
    border-radius: 16px;
    margin: 0 -4px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    padding: 12px 16px;
  }
  
  .stat-value {
    font-size: 16px;
  }
  
  .professional-main-chart,
  .professional-compare-chart {
    height: 280px;
  }
  
  .control-label {
    font-size: 13px;
    padding-left: 16px;
  }
  
  .control-label::before {
    width: 10px;
  }
}
</style>