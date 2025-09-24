<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'ComparisonAnalysis'
});

interface Props {
  healthData: any;
  healthMetrics: any;
  metricsConfig: any;
  searchParams: any;
}

const props = defineProps<Props>();

const comparisonType = ref<'period' | 'metrics' | 'target'>('period');
const selectedMetrics = ref<string[]>(['heart_rate', 'blood_oxygen', 'temperature']);
const showTarget = ref(true);

// 时期对比图表
const { domRef: periodChartRef, updateOptions: updatePeriodChart } = useEcharts(() => ({
  title: {
    text: '时期对比分析',
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold'
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
    left: 'center'
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
    data: [],
    axisLabel: {
      fontSize: 11
    }
  },
  yAxis: {
    type: 'value',
    name: '数值',
    axisLabel: {
      fontSize: 11
    }
  },
  series: []
}));

// 指标对比雷达图
const { domRef: radarChartRef, updateOptions: updateRadarChart } = useEcharts(() => ({
  title: {
    text: '多指标雷达分析',
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold'
    }
  },
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1
  },
  legend: {
    show: true,
    top: '10%',
    left: 'center'
  },
  radar: {
    indicator: [],
    center: ['50%', '60%'],
    radius: '60%',
    splitNumber: 5,
    splitLine: {
      lineStyle: {
        color: '#e8e8e8'
      }
    },
    splitArea: {
      areaStyle: {
        color: ['rgba(114, 172, 209, 0.1)', 'rgba(255, 255, 255, 0.1)']
      }
    },
    axisLine: {
      lineStyle: {
        color: '#bbb'
      }
    }
  },
  series: []
}));

// 目标达成图表
const { domRef: targetChartRef, updateOptions: updateTargetChart } = useEcharts(() => ({
  title: {
    text: '目标达成率分析',
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold'
    }
  },
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e8e8e8',
    borderWidth: 1,
    formatter: '{a} <br/>{b}: {c}% ({d}%)'
  },
  legend: {
    show: true,
    top: '10%',
    left: 'center'
  },
  series: [
    {
      name: '目标达成',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '60%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '14',
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

// 更新时期对比图表
function updatePeriodChartData() {
  if (!props.healthData.timestamps.length) return;

  const series = [];
  
  // 模拟本周数据（实际应该从API获取）
  const thisWeekData = props.healthData.heartRate.slice(-7);
  const lastWeekData = thisWeekData.map(val => val * (0.9 + Math.random() * 0.2));
  
  series.push({
    name: '本周',
    type: 'line',
    smooth: true,
    lineStyle: {
      width: 3,
      color: '#1890ff'
    },
    data: thisWeekData
  });

  series.push({
    name: '上周',
    type: 'line',
    smooth: true,
    lineStyle: {
      width: 3,
      color: '#52c41a',
      type: 'dashed'
    },
    data: lastWeekData
  });

  updatePeriodChart(opts => {
    opts.xAxis.data = props.healthData.timestamps.slice(-7);
    opts.series = series;
    return opts;
  });
}

// 更新雷达图
function updateRadarChartData() {
  const indicators = selectedMetrics.value.map(key => {
    const config = props.metricsConfig[key];
    return {
      name: config?.name || key,
      max: config?.normal?.max || 100,
      color: config?.color || '#1890ff'
    };
  });

  const currentData = selectedMetrics.value.map(key => {
    const current = props.healthMetrics.current[key];
    const config = props.metricsConfig[key];
    if (current && config?.normal?.max) {
      return (current / config.normal.max) * 100;
    }
    return 0;
  });

  const averageData = selectedMetrics.value.map(key => {
    const average = props.healthMetrics.average[key];
    const config = props.metricsConfig[key];
    if (average && config?.normal?.max) {
      return (average / config.normal.max) * 100;
    }
    return 0;
  });

  const series = [
    {
      name: '当前值',
      type: 'radar',
      data: [
        {
          value: currentData,
          name: '当前值',
          itemStyle: {
            color: '#1890ff'
          },
          areaStyle: {
            color: 'rgba(24, 144, 255, 0.2)'
          }
        }
      ]
    },
    {
      name: '平均值',
      type: 'radar',
      data: [
        {
          value: averageData,
          name: '平均值',
          itemStyle: {
            color: '#52c41a'
          },
          areaStyle: {
            color: 'rgba(82, 196, 26, 0.2)'
          }
        }
      ]
    }
  ];

  updateRadarChart(opts => {
    opts.radar.indicator = indicators;
    opts.series = series;
    return opts;
  });
}

// 更新目标达成图表
function updateTargetChartData() {
  const metrics = props.healthMetrics;
  const targetData = [];
  
  let achieved = 0;
  let total = 0;
  
  Object.keys(metrics.status || {}).forEach(key => {
    const status = metrics.status[key];
    total++;
    if (status === 'normal') {
      achieved++;
    }
  });

  const achievementRate = total > 0 ? (achieved / total) * 100 : 0;
  const failureRate = 100 - achievementRate;

  targetData.push(
    {
      value: achievementRate,
      name: '目标达成',
      itemStyle: {
        color: '#52c41a'
      }
    },
    {
      value: failureRate,
      name: '待改善',
      itemStyle: {
        color: '#f5222d'
      }
    }
  );

  updateTargetChart(opts => {
    opts.series[0].data = targetData;
    return opts;
  });
}

// 监听数据变化
watch(() => props.healthData, () => {
  updatePeriodChartData();
  updateRadarChartData();
  updateTargetChartData();
}, { deep: true, immediate: true });

watch(() => props.healthMetrics, () => {
  updateRadarChartData();
  updateTargetChartData();
}, { deep: true, immediate: true });

watch(() => selectedMetrics.value, updateRadarChartData, { deep: true });

// 计算对比统计
const comparisonStats = computed(() => {
  const stats = {
    improved: 0,
    declined: 0,
    stable: 0,
    total: 0
  };

  Object.values(props.healthMetrics.trend || {}).forEach((trend: any) => {
    stats.total++;
    if (trend === 'up') stats.improved++;
    else if (trend === 'down') stats.declined++;
    else stats.stable++;
  });

  return stats;
});

// 获取建议
const comparisonAdvice = computed(() => {
  const advice = [];
  const metrics = props.healthMetrics;
  
  if (comparisonStats.value.declined > comparisonStats.value.improved) {
    advice.push('多项指标呈下降趋势，建议加强健康管理');
  } else if (comparisonStats.value.improved > comparisonStats.value.declined) {
    advice.push('健康状况整体向好，请继续保持良好习惯');
  } else {
    advice.push('健康状况保持稳定，适当调整可以进一步改善');
  }

  Object.keys(metrics.status || {}).forEach(key => {
    const status = metrics.status[key];
    if (status === 'danger') {
      const config = props.metricsConfig[key];
      advice.push(`${config?.name || key}需要重点关注和改善`);
    }
  });

  return advice;
});
</script>

<template>
  <div class="comparison-analysis">
    <!-- 对比类型选择 -->
    <NCard class="comparison-controls">
      <div class="controls-header">
        <h3>对比分析类型</h3>
        <NButtonGroup size="small">
          <NButton 
            :type="comparisonType === 'period' ? 'primary' : 'default'"
            @click="comparisonType = 'period'"
          >
            时期对比
          </NButton>
          <NButton 
            :type="comparisonType === 'metrics' ? 'primary' : 'default'"
            @click="comparisonType = 'metrics'"
          >
            指标对比
          </NButton>
          <NButton 
            :type="comparisonType === 'target' ? 'primary' : 'default'"
            @click="comparisonType = 'target'"
          >
            目标达成
          </NButton>
        </NButtonGroup>
      </div>

      <!-- 指标选择 -->
      <div v-if="comparisonType === 'metrics'" class="metrics-selector">
        <label class="selector-label">选择对比指标</label>
        <NCheckboxGroup v-model:value="selectedMetrics">
          <div class="metrics-grid">
            <NCheckbox 
              v-for="(config, key) in metricsConfig" 
              :key="key"
              :value="key"
              :label="config.name"
            />
          </div>
        </NCheckboxGroup>
      </div>
    </NCard>

    <!-- 对比统计 -->
    <NCard class="comparison-stats">
      <template #header>
        <div class="stats-header">
          <NIcon size="18" color="#1890ff">
            <i class="i-material-symbols:analytics"></i>
          </NIcon>
          <span>对比统计</span>
        </div>
      </template>
      
      <div class="stats-grid">
        <div class="stat-item improved">
          <div class="stat-icon">
            <NIcon size="24" color="#52c41a">
              <i class="i-material-symbols:trending-up"></i>
            </NIcon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ comparisonStats.improved }}</div>
            <div class="stat-label">改善指标</div>
          </div>
        </div>
        
        <div class="stat-item declined">
          <div class="stat-icon">
            <NIcon size="24" color="#f5222d">
              <i class="i-material-symbols:trending-down"></i>
            </NIcon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ comparisonStats.declined }}</div>
            <div class="stat-label">下降指标</div>
          </div>
        </div>
        
        <div class="stat-item stable">
          <div class="stat-icon">
            <NIcon size="24" color="#faad14">
              <i class="i-material-symbols:trending-flat"></i>
            </NIcon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ comparisonStats.stable }}</div>
            <div class="stat-label">稳定指标</div>
          </div>
        </div>
        
        <div class="stat-item total">
          <div class="stat-icon">
            <NIcon size="24" color="#1890ff">
              <i class="i-material-symbols:dashboard"></i>
            </NIcon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ comparisonStats.total }}</div>
            <div class="stat-label">总指标数</div>
          </div>
        </div>
      </div>
    </NCard>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 时期对比图 -->
      <NCard v-if="comparisonType === 'period'" class="chart-card">
        <div ref="periodChartRef" class="comparison-chart"></div>
      </NCard>

      <!-- 雷达对比图 -->
      <NCard v-if="comparisonType === 'metrics'" class="chart-card">
        <div ref="radarChartRef" class="comparison-chart"></div>
      </NCard>

      <!-- 目标达成图 -->
      <NCard v-if="comparisonType === 'target'" class="chart-card">
        <div ref="targetChartRef" class="comparison-chart"></div>
      </NCard>

      <!-- 建议卡片 -->
      <NCard class="advice-card">
        <template #header>
          <div class="advice-header">
            <NIcon size="18" color="#722ed1">
              <i class="i-material-symbols:psychology"></i>
            </NIcon>
            <span>智能建议</span>
          </div>
        </template>
        
        <div class="advice-content">
          <div 
            v-for="(advice, index) in comparisonAdvice" 
            :key="index"
            class="advice-item"
          >
            <div class="advice-icon">
              <NIcon size="16" color="#722ed1">
                <i class="i-material-symbols:lightbulb"></i>
              </NIcon>
            </div>
            <div class="advice-text">{{ advice }}</div>
          </div>
          
          <div v-if="comparisonAdvice.length === 0" class="no-advice">
            <NEmpty description="暂无智能建议" size="small" />
          </div>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.comparison-analysis {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comparison-controls {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.controls-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.metrics-selector {
  margin-top: 16px;
}

.selector-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.comparison-stats {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item.improved {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.stat-item.declined {
  background: #fff2f0;
  border: 1px solid #ffb3b3;
}

.stat-item.stable {
  background: #fffbe6;
  border: 1px solid #ffe58f;
}

.stat-item.total {
  background: #f0f5ff;
  border: 1px solid #91d5ff;
}

.stat-icon {
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #262626;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.chart-card,
.advice-card {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.comparison-chart {
  height: 400px;
  width: 100%;
}

.advice-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.advice-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 360px;
  overflow-y: auto;
}

.advice-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.advice-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.advice-text {
  flex: 1;
  line-height: 1.5;
  color: #262626;
  font-size: 14px;
}

.no-advice {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .controls-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>